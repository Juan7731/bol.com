"""
Order processing pipeline for Bol.com orders.

Responsibilities:
- Fetch open orders from Bol API
- Classify into Single / SingleLine / Multi
- Generate Excel (.xlsx) files with required layout
- Upload generated files to SFTP
- Send email summary
- (Optional) run automatically at configured times
"""

import os
import sys
import logging
import traceback
import time as time_module
from datetime import datetime, date
from typing import List, Dict, Tuple, Optional

from bol_api_client import BolAPIClient
from bol_dtos import Order
from order_database import (
    init_database,
    mark_order_processed,
    get_unprocessed_orders,
)
from config import (
    BOL_CLIENT_ID,
    BOL_CLIENT_SECRET,
    TEST_MODE,
    PROCESS_TIMES,
    LOCAL_BATCH_DIR,
    SFTP_HOST,
    SFTP_PORT,
    SFTP_USERNAME,
    SFTP_PASSWORD,
    SFTP_REMOTE_BATCH_DIR,
    EMAIL_ENABLED,
    EMAIL_SMTP_HOST,
    EMAIL_SMTP_PORT,
    EMAIL_USE_TLS,
    EMAIL_USERNAME,
    EMAIL_PASSWORD,
    EMAIL_FROM,
    EMAIL_RECIPIENTS,
    EMAIL_SUBJECT_TEMPLATE,
    EMAIL_BODY_TEMPLATE,
    DEFAULT_SHOP_NAME,
)

import openpyxl
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

import paramiko
import smtplib
from smtplib import SMTP_SSL
from email.message import EmailMessage


logger = logging.getLogger(__name__)


def _ensure_directory(path: str) -> None:
    """Create directory if it does not exist."""
    os.makedirs(path, exist_ok=True)


def _today_batch_dir() -> str:
    """Return local directory path for today's batches."""
    today_str = date.today().strftime("%Y%m%d")
    batch_dir = os.path.join(LOCAL_BATCH_DIR, today_str)
    _ensure_directory(batch_dir)
    return batch_dir


def _determine_next_batch_number(batch_dir: str) -> str:
    """
    Determine next batch number for today based on existing files.
    
    Batch numbers reset daily starting from 001.
    All files generated in the same run share the same batch number:
    - First run of the day: 001 → S-001.xlsx, SL-001.xlsx, M-001.xlsx
    - Second run of the day: 002 → S-002.xlsx, SL-002.xlsx, M-002.xlsx
    - etc.

    Files are named like:
      S-001.xlsx, SL-001.xlsx, M-001.xlsx, S-002.xlsx, SL-002.xlsx, M-002.xlsx, ...
    """
    existing = [f for f in os.listdir(batch_dir) if f.endswith(".xlsx")]
    numbers = []
    for name in existing:
        try:
            base = os.path.splitext(name)[0]
            # Extract number from filename: S-001 → 001, SL-002 → 002
            _, num_str = base.split("-", 1)
            numbers.append(int(num_str))
        except (ValueError, IndexError):
            continue
    # Next batch number is max + 1, or 001 if no files exist
    next_num = max(numbers) + 1 if numbers else 1
    return f"{next_num:03d}"  # Format as 001, 002, 003, etc.


def classify_orders(orders: List[Order]) -> Dict[str, List[Order]]:
    """Group orders into Single, SingleLine, Multi based on DTO properties."""
    groups: Dict[str, List[Order]] = {"Single": [], "SingleLine": [], "Multi": []}
    for order in orders:
        cat = order.category
        if cat in groups:
            groups[cat].append(order)
    return groups


def _fetch_zpl_label(client: BolAPIClient, order_item_id: str) -> str:
    """
    Fetch ZPL shipping label for an order item using 'verzenden via bol'
    
    Args:
        client: Bol.com API client
        order_item_id: Order item ID
        
    Returns:
        ZPL label data as string, or empty string if failed
    """
    import base64
    
    try:
        logger.info(f"Fetching ZPL label for order item {order_item_id} using 'verzenden via bol'...")
        
        # Create shipping label (will use 'verzenden via bol' automatically)
        label_response = client.create_shipping_label(order_item_id)
        
        # Get shipment ID from response - try multiple possible structures
        shipment_id = None
        
        # Try direct shipmentId
        if 'shipmentId' in label_response:
            shipment_id = label_response.get('shipmentId')
        
        # Try shipments array
        if not shipment_id and 'shipments' in label_response:
            shipments = label_response.get('shipments', [])
            if shipments:
                shipment_id = shipments[0].get('shipmentId')
        
        # Try processStatus.shipmentId
        if not shipment_id and 'processStatus' in label_response:
            process_status = label_response.get('processStatus', {})
            shipment_id = process_status.get('shipmentId')
        
        if not shipment_id:
            logger.warning(f"No shipment ID in label response for order item {order_item_id}")
            logger.info(f"Label response structure: {list(label_response.keys())}")
            
            # Try to get shipment ID from shipments list after creation
            # Sometimes we need to query shipments for the order item
            try:
                # Get shipments for this order item's order
                # First, we need the order ID - but we don't have it here
                # Try alternative: check if label is in response directly
                if 'label' in label_response:
                    label_obj = label_response.get('label', {})
                    label_data = label_obj.get('data') or label_obj.get('labelData')
                    if label_data:
                        try:
                            zpl_data = base64.b64decode(label_data).decode('utf-8')
                            logger.info(f"✅ Found ZPL label directly in response ({len(zpl_data)} chars)")
                            return zpl_data
                        except:
                            return str(label_data) if label_data else ""
                
                # Check for labelData at root
                if 'labelData' in label_response:
                    label_data = label_response.get('labelData')
                    try:
                        zpl_data = base64.b64decode(label_data).decode('utf-8')
                        logger.info(f"✅ Found ZPL label in labelData ({len(zpl_data)} chars)")
                        return zpl_data
                    except:
                        return str(label_data) if label_data else ""
                
                # Log full response for debugging (first 500 chars)
                response_str = str(label_response)[:500]
                logger.debug(f"Full response (first 500 chars): {response_str}")
                
            except Exception as e:
                logger.debug(f"Error checking response structure: {e}")
            
            # If we still don't have shipment ID, try to get it from shipments list
            # This might require querying by order ID, which we don't have in this context
            return ""
        
        logger.info(f"Created shipment {shipment_id}, fetching ZPL label...")
        
        # Get the actual label data (ZPL)
        label_data_response = client.get_shipping_label(shipment_id)
        
        # Extract ZPL data - try multiple possible response structures
        label_data = None
        
        # Try direct label.data
        if 'label' in label_data_response:
            label_data = label_data_response.get('label', {}).get('data')
        
        # Try shipments[0].label.data
        if not label_data and 'shipments' in label_data_response:
            shipments = label_data_response.get('shipments', [])
            if shipments:
                label_data = shipments[0].get('label', {}).get('data')
        
        # Try direct data field
        if not label_data:
            label_data = label_data_response.get('data')
        
        if label_data:
            # If base64 encoded, decode it
            try:
                zpl_data = base64.b64decode(label_data).decode('utf-8')
                logger.info(f"✅ Successfully fetched ZPL label for order item {order_item_id} ({len(zpl_data)} chars)")
                return zpl_data
            except Exception as decode_error:
                # If decoding fails, might already be plain text
                try:
                    # Try as plain text
                    zpl_data = str(label_data)
                    if zpl_data.startswith('^XA') or 'ZPL' in zpl_data.upper():
                        logger.info(f"✅ Fetched ZPL label (plain text) for order item {order_item_id} ({len(zpl_data)} chars)")
                        return zpl_data
                    else:
                        logger.warning(f"Label data doesn't look like ZPL for {order_item_id}")
                        return zpl_data  # Return anyway
                except Exception as e:
                    logger.warning(f"Error processing label data for {order_item_id}: {e}")
                    return ""
        
        logger.warning(f"No label data in response for order item {order_item_id}")
        logger.debug(f"Label response structure: {list(label_data_response.keys())}")
        return ""
        
    except Exception as e:
        logger.error(f"Failed to fetch ZPL label for order item {order_item_id}: {e}")
        logger.debug(traceback.format_exc())
        return ""


def _create_workbook_for_category(
    category: str,
    batch_number: str,
    orders: List[Order],
    client: Optional[BolAPIClient] = None,
    filename_prefix: Optional[str] = None,
) -> Workbook:
    """
    Build an Excel workbook for a given category.

    Columns:
    A: Bol.com order ID
    B: Shop (Jean or Trivium)
    C: MP EAN
    D: Quantity of products for that EAN
    E: Shipping label (ZPL)
    F: Time of order
    G: Category (Single, SingleLine, Multi)
    H: Batch number (e.g. 001)
    I: Bol.com order status (open)
    """
    wb = openpyxl.Workbook()
    ws: Worksheet = wb.active
    ws.title = category

    # Header row - DO NOT CHANGE THESE NAMES (per requirements)
    headers = [
        "Order ID",
        "Shop",
        "MP EAN",
        "Quantity",
        "Shipping Label",
        "Order Time",
        "Batch Type",  # Must match file name (Single, SingleLine, Multi)
        "Batch Number",
        "Order Status",
    ]
    ws.append(headers)

    for order in orders:
        order_time_str = (
            order.order_placed_date_time.strftime("%Y-%m-%d %H:%M:%S")
            if order.order_placed_date_time
            else ""
        )
        for item in order.order_items:
            # Fetch ZPL label if client is provided
            zpl_label = ""
            if client:
                zpl_label = _fetch_zpl_label(client, item.order_item_id)
                if not zpl_label:
                    logger.warning(f"Failed to fetch ZPL label for order item {item.order_item_id}")
            
            # Batch Number column should contain full filename without extension (e.g., "S-001", "SL-001", "M-001")
            batch_number_full = f"{filename_prefix}-{batch_number}" if filename_prefix else batch_number
            
            row = [
                order.order_id,
                DEFAULT_SHOP_NAME,  # Shop name (Jean or Trivium)
                item.ean,
                item.quantity,
                zpl_label,  # ZPL shipping label
                order_time_str,
                category,  # This goes in "Batch Type" column (Single, SingleLine, Multi)
                batch_number_full,  # Full filename without extension (e.g., "S-001", "SL-001", "M-001")
                order.status.lower() if order.status else "open",  # Status should be lowercase "open"
            ]
            ws.append(row)
            
            # Mark order item as processed
            mark_order_processed(
                order.order_id,
                batch_number,
                category,
                order_item_id=item.order_item_id
            )

    return wb


def generate_excel_batches(
    grouped_orders: Dict[str, List[Order]],
    client: Optional[BolAPIClient] = None,
) -> Tuple[List[str], int]:
    """
    Generate Excel files for each category that has orders.
    
    IMPORTANT: All files generated in the same run use the SAME batch number.
    - Morning run: S-001.xlsx, SL-001.xlsx, M-001.xlsx (all with batch number "001")
    - Afternoon run: S-002.xlsx, SL-002.xlsx, M-002.xlsx (all with batch number "002")
    
    The batch number in the Excel file's "Batch Number" column MUST match the filename.

    Returns:
        (list of file paths created, total_orders_in_all_files)
    """
    batch_dir = _today_batch_dir()
    # Determine batch number ONCE per run - all files in this run use the same number
    batch_number = _determine_next_batch_number(batch_dir)
    logger.info(f"Using batch number: {batch_number} for this processing run")

    files_created: List[str] = []
    total_orders = 0

    # Generate files for each category - all use the SAME batch_number
    for category, prefix in [("Single", "S"), ("SingleLine", "SL"), ("Multi", "M")]:
        orders = grouped_orders.get(category, [])
        if not orders:
            continue

        # Filename format: S-001.xlsx, SL-001.xlsx, M-001.xlsx
        filename = f"{prefix}-{batch_number}.xlsx"
        
        # Create workbook with batch_number and prefix
        # Batch Number column will contain full filename without extension (e.g., "S-001", "SL-001", "M-001")
        wb = _create_workbook_for_category(category, batch_number, orders, client, filename_prefix=prefix)
        
        full_path = os.path.join(batch_dir, filename)
        wb.save(full_path)
        files_created.append(full_path)
        total_orders += len(orders)
        logger.info("Generated %s with %d orders (batch number in column: %s)", filename, len(orders), f"{prefix}-{batch_number}")

    return files_created, total_orders


def upload_files_sftp(file_paths: List[str]) -> None:
    """
    Upload generated files to the configured SFTP server.
    Verifies each upload was successful.
    """
    if not file_paths:
        logger.info("No files to upload to SFTP.")
        return

    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    uploaded_count = 0
    failed_count = 0
    
    try:
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        logger.info("Connected to SFTP server: %s:%d", SFTP_HOST, SFTP_PORT)

        # Ensure remote directory exists (best-effort)
        try:
            sftp.chdir(SFTP_REMOTE_BATCH_DIR)
            logger.info("Remote directory exists: %s", SFTP_REMOTE_BATCH_DIR)
        except IOError:
            # Try to create directories recursively
            logger.info("Creating remote directory: %s", SFTP_REMOTE_BATCH_DIR)
            parts = SFTP_REMOTE_BATCH_DIR.strip("/").split("/")
            current = ""
            for part in parts:
                current = f"{current}/{part}" if current else f"/{part}"
                try:
                    sftp.chdir(current)
                except IOError:
                    sftp.mkdir(current)
                    sftp.chdir(current)
                    logger.info("Created directory: %s", current)

        # Upload each file
        for local_path in file_paths:
            if not os.path.exists(local_path):
                logger.error("Local file does not exist: %s", local_path)
                failed_count += 1
                continue
                
            filename = os.path.basename(local_path)
            remote_path = os.path.join(SFTP_REMOTE_BATCH_DIR, filename).replace("\\", "/")
            
            try:
                logger.info("Uploading %s to %s", filename, remote_path)
                sftp.put(local_path, remote_path)
                
                # Verify upload by checking file exists and size matches
                try:
                    remote_stat = sftp.stat(remote_path)
                    local_size = os.path.getsize(local_path)
                    if remote_stat.st_size == local_size:
                        logger.info("✅ Successfully uploaded %s (%d bytes)", filename, local_size)
                        uploaded_count += 1
                    else:
                        logger.warning(
                            "⚠️ Upload size mismatch for %s: local=%d, remote=%d",
                            filename, local_size, remote_stat.st_size
                        )
                        uploaded_count += 1  # Still count as uploaded
                except Exception as verify_error:
                    logger.warning("Could not verify upload for %s: %s", filename, verify_error)
                    uploaded_count += 1  # Assume uploaded if we can't verify
                    
            except Exception as upload_error:
                logger.error("❌ Failed to upload %s: %s", filename, upload_error)
                failed_count += 1
                
    except Exception as e:
        logger.error("❌ SFTP connection/upload error: %s", e)
        failed_count = len(file_paths)
    finally:
        transport.close()
        logger.info(
            "SFTP upload complete: %d successful, %d failed out of %d total",
            uploaded_count, failed_count, len(file_paths)
        )


def send_summary_email(total_orders: int, file_paths: List[str]) -> None:
    """Send an email summary using configured SMTP settings."""
    if not EMAIL_ENABLED:
        logger.info("Email sending disabled in configuration.")
        return

    if not EMAIL_RECIPIENTS:
        logger.warning("EMAIL_ENABLED is True but EMAIL_RECIPIENTS is empty.")
        return

    subject = EMAIL_SUBJECT_TEMPLATE.replace("[total_orders]", str(total_orders))
    body = EMAIL_BODY_TEMPLATE.replace("[total_orders]", str(total_orders))

    if file_paths:
        body += "\n\nGenerated files:\n"
        for path in file_paths:
            body += f"- {os.path.basename(path)}\n"

    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(EMAIL_RECIPIENTS)
    msg["Subject"] = subject
    msg.set_content(body)

    logger.info("Sending summary email to %s", EMAIL_RECIPIENTS)

    # Use SSL for port 465, otherwise use SMTP with optional STARTTLS
    if EMAIL_SMTP_PORT == 465:
        with SMTP_SSL(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT) as server:
            if EMAIL_USERNAME:
                server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)
    else:
        with smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT) as server:
            if EMAIL_USE_TLS:
                server.starttls()
            if EMAIL_USERNAME:
                server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)


def run_processing_once() -> None:
    """Run one full processing cycle: fetch, classify, Excel, upload, email."""
    logger.info("Starting Bol.com order processing run...")
    
    # Initialize database
    init_database()

    client = BolAPIClient(BOL_CLIENT_ID, BOL_CLIENT_SECRET, test_mode=TEST_MODE)
    raw_orders = client.get_all_open_orders()
    all_orders = [Order.from_dict(o) for o in raw_orders]

    if not all_orders:
        logger.info("No open orders to process.")
        return
    
    # Filter out already processed orders
    order_ids = [order.order_id for order in all_orders]
    unprocessed_order_ids = get_unprocessed_orders(order_ids)
    
    # Keep only unprocessed orders
    orders = [order for order in all_orders if order.order_id in unprocessed_order_ids]
    
    if not orders:
        logger.info("No new unprocessed orders to process.")
        return
    
    logger.info(f"Processing {len(orders)} new orders (filtered from {len(all_orders)} total)")

    grouped = classify_orders(orders)
    files_created, total_orders = generate_excel_batches(grouped, client)

    if files_created:
        upload_files_sftp(files_created)
    else:
        logger.info("No Excel files generated (no orders in any category).")

    send_summary_email(total_orders, files_created)
    logger.info("Processing run completed. Orders processed: %d", total_orders)


def _normalize_time_string(t: str) -> str:
    """Return HH:MM (24h) or empty string if invalid/blank."""
    t = (t or "").strip()
    if not t:
        return ""
    try:
        dt = datetime.strptime(t, "%H:%M")
        return dt.strftime("%H:%M")
    except ValueError:
        return ""


def run_scheduler() -> None:
    """
    Simple in-process scheduler:
    - Reads up to four times from PROCESS_TIMES (HH:MM strings)
    - Runs processing once at each time per day

    NOTE: In production you can instead call run_processing_once()
    directly via cron at the desired times.
    """
    times = [_normalize_time_string(t) for t in PROCESS_TIMES]
    times = [t for t in times if t]
    if not times:
        logger.warning("No valid PROCESS_TIMES configured; scheduler will not run.")
        return

    logger.info("Starting scheduler with times: %s", ", ".join(times))

    last_run: Dict[str, date] = {}  # time_str -> date when last run

    try:
        while True:
            now = datetime.now()
            current_hm = now.strftime("%H:%M")
            today = now.date()

            if current_hm in times:
                if last_run.get(current_hm) != today:
                    logger.info("Triggering scheduled run for %s", current_hm)
                    run_processing_once()
                    last_run[current_hm] = today

            # Sleep 30 seconds between checks
            time_module.sleep(30)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--scheduler":
        # Run as long-running scheduler
        logger.info("Starting scheduler mode (press Ctrl+C to stop)...")
        run_scheduler()
    else:
        # Run a single processing cycle (default behavior)
        logger.info("Running single processing cycle (use --scheduler flag for continuous mode)")
        run_processing_once()


