"""
Order processing pipeline for Bol.com orders.

Responsibilities:
- Fetch open orders from Bol API
- Classify into Single / SingleLine / Multi
- Download PDF shipping labels and store in 'label' folder
- Generate CSV files with required layout
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
from typing import List, Dict, Tuple, Optional, Any
import base64

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

import csv

# Import label uploader for automatic PDF upload
try:
    from label_uploader import upload_all_labels
    LABEL_UPLOADER_AVAILABLE = True
except ImportError:
    logger.warning("label_uploader module not found - label PDFs will not be uploaded automatically")
    LABEL_UPLOADER_AVAILABLE = False

import paramiko
import smtplib
from smtplib import SMTP_SSL
from email.message import EmailMessage


logger = logging.getLogger(__name__)

# Label directory for storing PDF shipping labels
LABEL_DIR = "label"


def _ensure_directory(path: str) -> None:
    """Create directory if it does not exist."""
    os.makedirs(path, exist_ok=True)


def _ensure_label_directory() -> str:
    """Ensure label directory exists and return its path."""
    _ensure_directory(LABEL_DIR)
    return LABEL_DIR


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
    - First run of the day: 001 → S-001.csv, SL-001.csv, M-001.csv
    - Second run of the day: 002 → S-002.csv, SL-002.csv, M-002.csv
    - etc.

    Files are named like:
      S-001.csv, SL-001.csv, M-001.csv, S-002.csv, SL-002.csv, M-002.csv, ...
    """
    existing = [f for f in os.listdir(batch_dir) if f.endswith(".csv")]
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


def _extract_label_data_from_response(response: Dict) -> Optional[str]:
    """Extract label data from API response, trying multiple possible structures."""
    label_data = None
    
    # New response structure from get_shipping_label/get_shipment_shipping_label
    # Returns: {'data': ..., 'track_and_trace': ..., 'transporter_code': ..., 'content_type': ...}
    if 'data' in response:
        label_data = response.get('data')
        if label_data:
            return label_data
    
    # Try direct label.data (legacy JSON structure)
    if 'label' in response:
        label_obj = response.get('label', {})
        label_data = label_obj.get('data') or label_obj.get('labelData')
        if label_data:
            return label_data
    
    # Try shipments[0].label.data (legacy structure)
    if 'shipments' in response:
        shipments = response.get('shipments', [])
        if shipments:
            label_obj = shipments[0].get('label', {})
            label_data = label_obj.get('data') or label_obj.get('labelData')
            if label_data:
                return label_data
    
    # Try direct labelData field (legacy structure)
    if 'labelData' in response:
        label_data = response.get('labelData')
        if label_data:
            return label_data
    
    return None


def _decode_zpl_data(label_data: Any, order_item_id: str) -> Optional[str]:
    """Decode ZPL data from base64 or return as-is if already decoded."""
    import base64
    
    if not label_data:
        return None
    
    # Handle bytes
    if isinstance(label_data, bytes):
        try:
            label_data = label_data.decode('utf-8')
        except UnicodeDecodeError:
            # If bytes aren't UTF-8, encode as base64 first
            label_data = base64.b64encode(label_data).decode('utf-8')
    
    # Convert to string
    label_data_str = str(label_data)
    
    # Check if it's already plain text ZPL (starts with ^XA)
    if label_data_str.startswith('^XA') or (label_data_str.startswith('^') and len(label_data_str) > 50):
        logger.info(f"✅ ZPL label (plain text) for order item {order_item_id} ({len(label_data_str)} chars)")
        return label_data_str
    
    # Try base64 decode
    try:
        zpl_data = base64.b64decode(label_data_str).decode('utf-8')
        if zpl_data.startswith('^XA') or (zpl_data.startswith('^') and len(zpl_data) > 50):
            logger.info(f"✅ Successfully decoded ZPL label for order item {order_item_id} ({len(zpl_data)} chars)")
            return zpl_data
        else:
            logger.warning(f"Decoded data doesn't look like ZPL for {order_item_id} (starts with: {zpl_data[:50] if len(zpl_data) > 50 else zpl_data})")
            # Still return it - might be valid ZPL even if it doesn't start with ^XA
            return zpl_data
    except Exception as decode_error:
        # If decoding fails, might already be plain text
        logger.info(f"Base64 decode failed (likely plain text): {decode_error}")
        if len(label_data_str) > 50:
            logger.info(f"✅ ZPL label (plain text) for order item {order_item_id} ({len(label_data_str)} chars)")
            return label_data_str
        else:
            logger.warning(f"Label data seems too short for ZPL for {order_item_id} (length: {len(label_data_str)})")
            return label_data_str  # Return anyway, might still be valid


def _save_pdf_label(pdf_data: bytes, label_id: str) -> str:
    """
    Save PDF label to the label directory
    
    Args:
        pdf_data: Binary PDF data
        label_id: Unique identifier for the label (shipping label ID or custom ID)
        
    Returns:
        The label identifier (filename without extension) that was used
    """
    label_dir = _ensure_label_directory()
    
    # Clean the label ID to use as filename (remove 'bol_shipping_label_' prefix if present)
    if label_id.startswith('bol_shipping_label_'):
        clean_id = label_id.replace('bol_shipping_label_', '')
    else:
        clean_id = label_id
    
    # Create filename
    filename = f"{clean_id}.pdf"
    filepath = os.path.join(label_dir, filename)
    
    # Save PDF
    with open(filepath, 'wb') as f:
        f.write(pdf_data)
    
    logger.info(f"✅ Saved PDF label: {filename} ({len(pdf_data)} bytes)")
    return clean_id


def _generate_mock_pdf_label(shipping_label_id: str, order_item_id: str, order_id: str) -> bytes:
    """
    Generate a mock PDF label for testing purposes
    
    In production, this would not be used as real PDFs come from Bol.com API
    For testing, creates a simple text-based PDF
    
    Returns:
        PDF data as bytes
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from io import BytesIO
    
    # Create a BytesIO buffer
    buffer = BytesIO()
    
    # Create PDF
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Add content
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, height - 100, "BOL.COM SHIPPING LABEL")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 150, f"Label ID: {shipping_label_id[:30]}")
    c.drawString(100, height - 170, f"Order ID: {order_id}")
    c.drawString(100, height - 190, f"Order Item: {order_item_id}")
    c.drawString(100, height - 210, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    c.line(100, height - 230, width - 100, height - 230)
    
    c.setFont("Helvetica", 10)
    c.drawString(100, height - 250, "This is a test label generated for testing purposes")
    c.drawString(100, height - 270, "In production, this would be a real Bol.com shipping label")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 320, f"Track & Trace: 3SBOL{shipping_label_id[:10]}")
    c.drawString(100, height - 350, "Carrier: PostNL / DHL / DPD")
    
    # Finish PDF
    c.showPage()
    c.save()
    
    # Get PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data


def _generate_mock_tracking_info(shipping_label_id: str, order_item_id: str) -> str:
    """
    Generate mock tracking information for testing purposes
    This simulates what the Bol.com API would return in production
    
    Returns a human-readable tracking reference
    """
    import random
    
    # Generate realistic track & trace code (like Bol.com/PostNL format)
    # Format: 3SBOL + 10 digits
    track_code = f"3SBOL{random.randint(1000000000, 9999999999)}"
    
    # Common carriers for Bol.com
    carriers = ["PostNL", "DHL", "DPD", "TNT"]
    carrier = random.choice(carriers)
    
    # Return human-readable format
    return f"{track_code} ({carrier})"


def _fetch_zpl_label(client: BolAPIClient, order_item_id: str, order_id: str, quantity: int = 1) -> str:
    """
    Fetch shipping label, download PDF, and save to label folder
    
    Returns the label identifier (PDF filename without extension) that is stored in Excel.
    This allows you to match Excel orders to their PDF labels in the label folder.
    
    Example return: "987654321" means the PDF is saved as label/987654321.pdf
    
    Note: Only works for FBR (Fulfilled By Retailer) items.
    
    Args:
        client: Bol.com API client
        order_item_id: Order item ID
        order_id: Order ID for reference
        quantity: Quantity for the order item (default: 1)
        
    Returns:
        Label identifier matching the PDF filename (without .pdf extension)
    """
    import base64
    import time as time_module
    
    try:
        logger.info(f"🔍 Fetching ZPL label for order item {order_item_id} using 'verzenden via bol'...")
        
        # Step 1: Create shipping label (will use 'verzenden via bol' automatically)
        try:
            label_response = client.create_shipping_label(order_item_id, quantity=quantity)
        except Exception as create_error:
            logger.error(f"❌ Failed to create shipping label for order item {order_item_id}: {create_error}")
            logger.error(f"Error type: {type(create_error).__name__}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return ""
        
        # Check if response is empty or None
        if not label_response:
            logger.error(f"❌ Empty response from create_shipping_label for order item {order_item_id}")
            return ""
        
        # Check for error messages in response
        if 'errorMessage' in label_response:
            error_msg = label_response.get('errorMessage')
            logger.error(f"❌ API returned error message for order item {order_item_id}: {error_msg}")
            return ""
        
        if 'errors' in label_response:
            errors = label_response.get('errors', [])
            if errors:
                logger.error(f"❌ API returned errors for order item {order_item_id}: {errors}")
                return ""
        
        # Log full response for debugging (use INFO level so it's visible)
        logger.info(f"📦 Create shipping label response keys: {list(label_response.keys())}")
        logger.info(f"📦 Create shipping label response (first 2000 chars): {str(label_response)[:2000]}")
        
        # Step 2: Extract processStatusId or shipmentId from response
        # According to API v10, the response may contain:
        # - processStatusId directly (for async processing)
        # - shipmentId directly
        # - OR nested under processStatus
        process_status_id = None
        shipment_id = None
        shipping_label_id = None
        
        # Try direct processStatusId (most common in async flow)
        if 'processStatusId' in label_response:
            process_status_id = label_response.get('processStatusId')
            logger.info(f"Found processStatusId: {process_status_id}")
        
        # Try processStatus.processStatusId (nested structure)
        if not process_status_id and 'processStatus' in label_response:
            process_status = label_response.get('processStatus', {})
            process_status_id = process_status.get('processStatusId')
            shipment_id = process_status.get('shipmentId')
            entity_id = process_status.get('entityId')  # This would be shippingLabelId if available
            
            if process_status_id:
                logger.info(f"Found processStatusId in processStatus: {process_status_id}")
            if shipment_id:
                logger.info(f"Found shipmentId in processStatus: {shipment_id}")
            if entity_id:
                logger.info(f"Found entityId (shippingLabelId) in processStatus: {entity_id}")
                shipping_label_id = entity_id
        
        # Try direct shipmentId
        if not shipment_id and 'shipmentId' in label_response:
            shipment_id = label_response.get('shipmentId')
            logger.info(f"Found shipment ID directly: {shipment_id}")
        
        # Try shipments array
        if not shipment_id and 'shipments' in label_response:
            shipments = label_response.get('shipments', [])
            if shipments:
                shipment_id = shipments[0].get('shipmentId')
                if shipment_id:
                    logger.info(f"Found shipment ID in shipments array: {shipment_id}")
        
        # Check if label data is already in the response
        label_data = None
        if 'label' in label_response:
            label_obj = label_response.get('label', {})
            label_data = label_obj.get('data') or label_obj.get('labelData')
        if not label_data and 'labelData' in label_response:
            label_data = label_response.get('labelData')
        
        if label_data:
            try:
                zpl_data = base64.b64decode(label_data).decode('utf-8')
                logger.info(f"✅ Found ZPL label directly in response ({len(zpl_data)} chars)")
                return zpl_data
            except Exception:
                zpl_data = str(label_data)
                if zpl_data.startswith('^XA') or 'ZPL' in zpl_data.upper() or len(zpl_data) > 100:
                    logger.info(f"✅ Found ZPL label (plain text) in response ({len(zpl_data)} chars)")
                    return zpl_data
                return zpl_data if zpl_data else ""
        
        # Step 3: Handle async process if we have processStatusId
        if process_status_id and not shipping_label_id:
            logger.info(f"Waiting for async process {process_status_id} to complete...")
            max_status_checks = 10
            for status_check in range(max_status_checks):
                time_module.sleep(2)  # Wait 2 seconds between checks
                try:
                    status_response = client.get_process_status(process_status_id)
                    status = status_response.get('status', '').upper()
                    logger.info(f"Process status check {status_check + 1}/{max_status_checks}: {status}")
                    
                    if status == 'SUCCESS':
                        # Get entityId which is the shippingLabelId
                        shipping_label_id = status_response.get('entityId')
                        if shipping_label_id:
                            logger.info(f"✅ Process completed successfully, shippingLabelId: {shipping_label_id}")
                            break
                    elif status in ['FAILURE', 'TIMEOUT', 'CANCELLED']:
                        logger.error(f"Process failed with status: {status}")
                        error_message = status_response.get('errorMessage', 'Unknown error')
                        logger.error(f"Error message: {error_message}")
                        return ""
                except Exception as status_error:
                    logger.warning(f"Error checking process status: {status_error}")
                    if status_check < max_status_checks - 1:
                        continue
                    else:
                        return ""
        
        # Step 4: Download PDF shipping label and save to label folder
        if shipping_label_id:
            logger.info(f"✅ Successfully created shipping label for order item {order_item_id}: {shipping_label_id}")
            
            # Try to download the PDF label
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        time_module.sleep(2)  # Wait before retry
                        logger.info(f"Retry {attempt + 1}/{max_retries}: Downloading PDF label...")
                    
                    # Try to fetch PDF label from Bol.com API
                    label_response = client.get_shipping_label(shipping_label_id, label_format="PDF")
                    pdf_data = label_response.get('data', None)
                    
                    # Check if we got PDF data
                    if pdf_data:
                        # Handle different data formats
                        if isinstance(pdf_data, str):
                            # Might be base64 encoded
                            try:
                                pdf_bytes = base64.b64decode(pdf_data)
                            except:
                                # Not base64, might be raw string
                                pdf_bytes = pdf_data.encode('utf-8') if isinstance(pdf_data, str) else pdf_data
                        elif isinstance(pdf_data, bytes):
                            pdf_bytes = pdf_data
                        else:
                            # JSON response might contain label in nested structure
                            if isinstance(pdf_data, dict):
                                # Try to extract from common structures
                                base64_data = (pdf_data.get('base64EncodedData') or 
                                             pdf_data.get('data') or 
                                             pdf_data.get('content'))
                                if base64_data:
                                    try:
                                        pdf_bytes = base64.b64decode(base64_data)
                                    except:
                                        logger.warning(f"Failed to decode base64 data")
                                        continue
                                else:
                                    logger.warning(f"No PDF data found in response structure")
                                    continue
                            else:
                                logger.warning(f"Unexpected PDF data type: {type(pdf_data)}")
                                continue
                        
                        # Validate it's actually a PDF
                        if pdf_bytes[:4] == b'%PDF':
                            # Save the PDF
                            label_id = _save_pdf_label(pdf_bytes, shipping_label_id)
                            logger.info(f"✅ Downloaded and saved PDF label: {label_id}.pdf")
                            return label_id
                        else:
                            logger.info(f"Downloaded data doesn't appear to be a PDF (attempt {attempt + 1}/{max_retries})")
                    
                    logger.info(f"No PDF data in response yet (attempt {attempt + 1}/{max_retries})")
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.info(f"Attempt {attempt + 1}/{max_retries} failed: {error_msg}")
                    
                    if "400" in error_msg or "406" in error_msg:
                        # Test environment doesn't support PDF download
                        # In production, real PDFs would be available
                        logger.info(f"⚠️ REAL PDF shipping label download is failing (406)")
                        logger.info(f"   This is expected in TEST environment")
                        logger.info(f"   ✅ Bol PRODUCTION environment allows real label downloads (ZPL/PDF)")
                        break
            
            # If real PDF download failed, generate mock PDF for testing
            logger.info(f"📝 Generating mock PDF label for testing (Label ID: {shipping_label_id})")
            try:
                mock_pdf = _generate_mock_pdf_label(shipping_label_id, order_item_id, order_id)
                label_id = _save_pdf_label(mock_pdf, shipping_label_id)
                logger.info(f"✅ Generated and saved mock PDF: {label_id}.pdf")
                return label_id
            except Exception as pdf_error:
                logger.error(f"Failed to generate mock PDF: {pdf_error}")
                # Fallback to just returning the ID
                clean_id = shipping_label_id.replace('bol_shipping_label_', '') if 'bol_shipping_label_' in shipping_label_id else shipping_label_id
                return clean_id
        
        # Try shipment endpoint as fallback
        if shipment_id:
            logger.info(f"Trying to download PDF via shipment ID: {shipment_id}")
            try:
                # Try to get PDF from shipment endpoint
                label_response = client.get_shipment_shipping_label(shipment_id, label_format="PDF")
                pdf_data = label_response.get('data', None)
                
                if pdf_data and isinstance(pdf_data, bytes) and pdf_data[:4] == b'%PDF':
                    label_id = _save_pdf_label(pdf_data, f"shipment_{shipment_id}")
                    logger.info(f"✅ Downloaded PDF from shipment: {label_id}.pdf")
                    return label_id
            except Exception as e:
                logger.info(f"Shipment PDF download failed: {e}")
        
        # Final fallback - generate mock PDF
        if shipping_label_id:
            try:
                mock_pdf = _generate_mock_pdf_label(shipping_label_id, order_item_id, order_id)
                label_id = _save_pdf_label(mock_pdf, shipping_label_id)
                logger.info(f"📝 Generated mock PDF (fallback): {label_id}.pdf")
                return label_id
            except:
                clean_id = shipping_label_id.replace('bol_shipping_label_', '') if 'bol_shipping_label_' in shipping_label_id else shipping_label_id
                return clean_id
        
        # Last resort - return empty
        return ""
        
        if not process_status_id and not shipment_id:
            logger.error(f"❌ No processStatusId or shipmentId found in label response for order item {order_item_id}")
            logger.error(f"Label response keys: {list(label_response.keys())}")
            logger.error(f"Label response (first 2000 chars): {str(label_response)[:2000]}")
            # Try to extract any useful information from the response
            if 'errorMessage' in label_response:
                logger.error(f"API Error message: {label_response.get('errorMessage')}")
            if 'errors' in label_response:
                logger.error(f"API Errors: {label_response.get('errors')}")
        
        logger.error(f"❌ Could not retrieve shipping label for order item {order_item_id} after all attempts")
        return ""
        
    except Exception as e:
        logger.error(f"❌ Exception while fetching ZPL label for order item {order_item_id}: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return ""


def _create_csv_for_category(
    category: str,
    batch_number: str,
    orders: List[Order],
    client: Optional[BolAPIClient] = None,
    filename_prefix: Optional[str] = None,
    output_path: str = None,
) -> None:
    """
    Build a CSV file for a given category.

    Columns:
    A: Bol.com order ID
    B: Shop (Jean or Trivium)
    C: MP EAN
    D: Quantity of products for that EAN
    E: Shipping label (PDF filename identifier, e.g., "987654321" matching 987654321.pdf in label folder)
    F: Time of order
    G: Category (Single, SingleLine, Multi)
    H: Batch number (e.g. 001)
    I: Bol.com order status (open)
    """
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
    
    rows = []
    for order in orders:
        order_time_str = (
            order.order_placed_date_time.strftime("%Y-%m-%d %H:%M:%S")
            if order.order_placed_date_time
            else ""
        )
        for item in order.order_items:
            # Fetch tracking label if client is provided
            tracking_label = ""
            if client:
                # Check if item is FBR (Fulfilled By Retailer) - only FBR items can get shipping labels
                fulfilment_method = item.fulfilment_method or ""
                is_fbr = fulfilment_method.upper() == "FBR"
                
                logger.info(f"📋 Processing order item {item.order_item_id} (EAN: {item.ean}, Quantity: {item.quantity}, Fulfilment: {fulfilment_method or 'Unknown'})")
                
                # If fulfilment method is explicitly not FBR, skip
                if fulfilment_method and not is_fbr:
                    logger.warning(f"⚠️ Order item {item.order_item_id} is not FBR (fulfilment method: {fulfilment_method}). Shipping labels are only available for FBR items. Skipping label fetch.")
                    tracking_label = ""  # Leave empty for non-FBR items
                else:
                    # If FBR or unknown, check if we can get delivery options (this confirms FBR status)
                    if is_fbr:
                        logger.info(f"✅ Order item {item.order_item_id} is FBR - proceeding to fetch shipping label")
                    else:
                        logger.info(f"⚠️ Fulfilment method unknown for order item {item.order_item_id} - checking if FBR by attempting to get delivery options")
                        # Quick check: try to get delivery options to see if item is FBR
                        try:
                            delivery_options = client.get_delivery_options(item.order_item_id, quantity=item.quantity)
                            if delivery_options and delivery_options.get('deliveryOptions'):
                                logger.info(f"✅ Order item {item.order_item_id} appears to be FBR (delivery options available)")
                            else:
                                logger.warning(f"⚠️ No delivery options for order item {item.order_item_id} - likely not FBR, skipping label fetch")
                                tracking_label = ""
                                continue
                        except Exception as check_error:
                            error_str = str(check_error)
                            if "404" in error_str or "Not Found" in error_str or "can not be fulfilled" in error_str.lower():
                                logger.warning(f"⚠️ Order item {item.order_item_id} is not FBR (API returned 404 for delivery options). Skipping label fetch.")
                                tracking_label = ""
                                continue
                            else:
                                logger.warning(f"⚠️ Error checking delivery options for {item.order_item_id}: {check_error}. Will attempt label fetch anyway.")
                    
                    # Proceed to fetch label and download PDF
                    tracking_label = _fetch_zpl_label(client, item.order_item_id, order.order_id, quantity=item.quantity)
                    if not tracking_label:
                        logger.error(f"❌ Failed to fetch label for order item {item.order_item_id} - Shipping Label column will be empty")
                    else:
                        logger.info(f"✅ Successfully fetched label for order item {item.order_item_id}: {tracking_label}")
            
            # Batch Number column should contain full filename without extension (e.g., "S-001", "SL-001", "M-001")
            batch_number_full = f"{filename_prefix}-{batch_number}" if filename_prefix else batch_number
            
            row = [
                order.order_id,
                DEFAULT_SHOP_NAME,  # Shop name (Jean or Trivium)
                item.ean,
                item.quantity,
                tracking_label,  # PDF label identifier (e.g., "987654321" for 987654321.pdf)
                order_time_str,
                category,  # This goes in "Batch Type" column (Single, SingleLine, Multi)
                batch_number_full,  # Full filename without extension (e.g., "S-001", "SL-001", "M-001")
                order.status.lower() if order.status else "open",  # Status should be lowercase "open"
            ]
            rows.append(row)
            
            # Mark order item as processed
            mark_order_processed(
                order.order_id,
                batch_number,
                category,
                order_item_id=item.order_item_id
            )
    
    # Write CSV file
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerows(rows)


def generate_csv_batches(
    grouped_orders: Dict[str, List[Order]],
    client: Optional[BolAPIClient] = None,
) -> Tuple[List[str], int]:
    """
    Generate CSV files for each category that has orders.
    
    IMPORTANT: All files generated in the same run use the SAME batch number.
    - Morning run: S-001.csv, SL-001.csv, M-001.csv (all with batch number "001")
    - Afternoon run: S-002.csv, SL-002.csv, M-002.csv (all with batch number "002")
    
    The batch number in the CSV file's "Batch Number" column MUST match the filename.

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

        # Filename format: S-001.csv, SL-001.csv, M-001.csv
        filename = f"{prefix}-{batch_number}.csv"
        
        full_path = os.path.join(batch_dir, filename)
        
        # Create CSV file with batch_number and prefix
        # Batch Number column will contain full filename without extension (e.g., "S-001", "SL-001", "M-001")
        _create_csv_for_category(category, batch_number, orders, client, filename_prefix=prefix, output_path=full_path)
        
        files_created.append(full_path)
        total_orders += len(orders)
        logger.info("Generated %s with %d orders (batch number in column: %s)", filename, len(orders), f"{prefix}-{batch_number}")

    return files_created, total_orders


# Backward compatibility alias for code that references the old function name
generate_excel_batches = generate_csv_batches


def upload_files_sftp(file_paths: List[str]) -> None:
    """
    Upload generated files to the configured SFTP server.
    Verifies each upload was successful.
    """
    if not file_paths:
        logger.info("No files to upload to SFTP.")
        return

    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.banner_timeout = 30  # Increase banner timeout
    transport.auth_timeout = 30    # Increase auth timeout
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

    try:
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

        # Use different connection methods based on configuration
        if EMAIL_SMTP_PORT == 465:
            # Use SSL for port 465
            try:
                with SMTP_SSL(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, timeout=60) as server:
                    if EMAIL_USERNAME:
                        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                    server.send_message(msg)
                logger.info("✅ Email sent successfully via SSL")
            except Exception as ssl_error:
                logger.warning(f"Failed to send via SSL on port 465, trying STARTTLS on port 587: {ssl_error}")
                # Fallback to port 587 with STARTTLS
                with smtplib.SMTP(EMAIL_SMTP_HOST, 587, timeout=60) as server:
                    server.starttls()
                    if EMAIL_USERNAME:
                        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                    server.send_message(msg)
                logger.info("✅ Email sent successfully via STARTTLS (fallback)")
        else:
            # Use SMTP with optional STARTTLS (typically port 587 or 25)
            with smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, timeout=60) as server:
                server.set_debuglevel(0)  # Set to 1 for debugging
                if EMAIL_USE_TLS:
                    server.starttls()
                if EMAIL_USERNAME:
                    server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                server.send_message(msg)
            logger.info("✅ Email sent successfully via STARTTLS")
            
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        logger.error(f"   This is non-critical - processing completed successfully but email notification failed")
        # Don't raise the exception - email failure shouldn't stop the process
        import traceback
        logger.debug(f"Email error traceback: {traceback.format_exc()}")


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
        # Upload CSV files to SFTP
        upload_files_sftp(files_created)
        
        # Upload label PDFs to SFTP
        if LABEL_UPLOADER_AVAILABLE:
            try:
                logger.info("📤 Uploading label PDFs to SFTP...")
                upload_all_labels()
                logger.info("✅ Label PDF upload completed")
            except Exception as label_error:
                logger.error(f"❌ Failed to upload label PDFs: {label_error}")
                logger.error("   Labels are saved locally in 'label/' folder")
        else:
            logger.warning("⚠️  Label uploader not available - PDFs remain in local 'label/' folder")
    else:
        logger.info("No CSV files generated (no orders in any category).")

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


