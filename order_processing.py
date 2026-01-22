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
from bol_dtos import Order, CustomerDetails
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
    PROCESS_INTERVAL,
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

# Initialize logger BEFORE using it
logger = logging.getLogger(__name__)

# Import label uploader for automatic PDF upload
try:
    from label_uploader import upload_all_labels, upload_labels_for_csv_files
    LABEL_UPLOADER_AVAILABLE = True
except ImportError:
    logger.warning("label_uploader module not found - label PDFs will not be uploaded automatically")
    LABEL_UPLOADER_AVAILABLE = False
    upload_labels_for_csv_files = None

import paramiko
import smtplib
from smtplib import SMTP_SSL
from email.message import EmailMessage

# Label directory for storing PDF shipping labels
LABEL_DIR = "label"


def _ensure_directory(path: str) -> None:
    """Create directory if it does not exist."""
    os.makedirs(path, exist_ok=True)


def _ensure_label_directory() -> str:
    """Ensure label directory exists and return its path."""
    _ensure_directory(LABEL_DIR)
    return LABEL_DIR


def _batch_dir() -> str:
    """Return local directory path for batches (no date subfolder)."""
    _ensure_directory(LOCAL_BATCH_DIR)
    return LOCAL_BATCH_DIR


def _determine_next_batch_number(batch_dir: str) -> str:
    """
    Determine next batch number for today based on existing files.
    
    Batch numbers reset daily starting from 001.
    All files generated in the same run share the same batch number:
    - First run of the day: 001 → S-001.csv, SL-001.csv, M-001.csv
    - Second run of the day: 002 → S-002.csv, SL-002.csv, M-002.csv
    - etc.
    - Next day: resets to 001

    Files are named like:
      S-001.csv, SL-001.csv, M-001.csv, S-002.csv, SL-002.csv, M-002.csv, ...
    """
    today = date.today()
    existing = [f for f in os.listdir(batch_dir) if f.endswith(".csv")]
    numbers = []
    for name in existing:
        try:
            base = os.path.splitext(name)[0]
            # Extract number from filename: S-001 → 001, SL-002 → 002
            _, num_str = base.split("-", 1)
            # Check if file was created today (by checking modification time)
            file_path = os.path.join(batch_dir, name)
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path)).date()
            if file_mtime == today:
                numbers.append(int(num_str))
        except (ValueError, IndexError, OSError):
            continue
    # Next batch number is max + 1, or 001 if no files exist today
    next_num = max(numbers) + 1 if numbers else 1
    return f"{next_num:03d}"  # Format as 001, 002, 003, etc.


def classify_orders(orders: List[Order]) -> Dict[str, List[Order]]:
    """Group orders into Single, SingleLine, Multi based on DTO properties."""
    groups: Dict[str, List[Order]] = {"Single": [], "SingleLine": [], "Multi": []}
    
    logger.info(f"📋 Classifying {len(orders)} order(s)...")
    
    for order in orders:
        cat = order.category
        logger.info(f"   Order {order.order_id}: {len(order.order_items)} item(s), Category: {cat}")
        
        # Log order item details for debugging
        if not order.order_items:
            logger.warning(f"   ⚠️ Order {order.order_id} has NO order items - cannot be classified")
            continue
        
        for idx, item in enumerate(order.order_items):
            logger.info(f"      Item {idx + 1}: orderItemId={item.order_item_id}, EAN={item.ean}, quantity={item.quantity}, fulfilment={item.fulfilment_method}")
        
        if cat in groups:
            groups[cat].append(order)
            logger.info(f"   ✅ Order {order.order_id} classified as {cat}")
        else:
            logger.warning(f"   ⚠️ Order {order.order_id} category '{cat}' not recognized - skipping")
    
    # Log classification summary
    total_classified = sum(len(groups[cat]) for cat in groups)
    logger.info(f"📋 Classification summary:")
    logger.info(f"   Single: {len(groups['Single'])} order(s)")
    logger.info(f"   SingleLine: {len(groups['SingleLine'])} order(s)")
    logger.info(f"   Multi: {len(groups['Multi'])} order(s)")
    logger.info(f"   Total classified: {total_classified} out of {len(orders)} order(s)")
    
    if total_classified == 0 and len(orders) > 0:
        logger.error(f"❌ No orders were classified! This means:")
        logger.error(f"   - Orders might not have order items")
        logger.error(f"   - Order items might not have EANs")
        logger.error(f"   - Order structure might be different than expected")
        logger.error(f"   - Check the logs above for order item details")
    
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


def _generate_production_pdf_label(shipping_label_id: str, order_item_id: str, order_id: str, 
                                   track_and_trace: Optional[str] = None, 
                                   transporter_code: Optional[str] = None,
                                   customer_details: Optional[Any] = None,
                                   quantity: int = 1) -> bytes:
    """
    [DEPRECATED - DO NOT USE]
    
    This function generates custom PDF labels which DO NOT meet carrier requirements.
    
    CRITICAL: Custom PDFs are NOT acceptable - carrier requires exact format from Bol.com API.
    This function is kept only for reference but should NEVER be called in production.
    
    Only OFFICIAL PDFs downloaded directly from Bol.com API are acceptable.
    Use get_shipping_label() with label_format="PDF" to get official labels.
    
    Args:
        shipping_label_id: Shipping label ID from Bol.com
        order_item_id: Order item ID
        order_id: Order ID
        track_and_trace: Real track & trace code from API (optional)
        transporter_code: Real transporter code from API (optional)
        customer_details: CustomerDetails object with recipient information (optional)
        quantity: Quantity of items in the shipment (default: 1)
    
    Returns:
        PDF data as bytes (but this PDF does NOT meet carrier requirements)
    """
    logger.error("⚠️  WARNING: Custom PDF generation called - this should NOT happen!")
    logger.error("   Custom PDFs do NOT meet carrier requirements")
    logger.error("   Only OFFICIAL PDFs from Bol.com API are acceptable")
    raise Exception("Custom PDF generation is not supported - only official PDFs from Bol.com API are acceptable")
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from io import BytesIO
    
    # Create a BytesIO buffer
    buffer = BytesIO()
    
    # Create PDF
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Determine transporter - default to POSTNL if not specified
    if transporter_code:
        # Map transporter codes to readable names
        transporter_map = {
            'POSTNL': 'POSTNL',
            'DHL': 'DHL',
            'DPD': 'DPD',
            'TNT': 'TNT',
            'UPS': 'UPS',
            'GLS': 'GLS'
        }
        carrier_display = transporter_map.get(transporter_code.upper(), transporter_code.upper())
        is_postnl = transporter_code.upper() == 'POSTNL'
    else:
        carrier_display = "POSTNL"  # Default to POSTNL
        is_postnl = True
    
    # Sender Information (Top Left)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(100, height - 50, "Afzender.")
    c.setFont("Helvetica", 10)
    c.drawString(100, height - 65, "Dormivo")
    c.drawString(100, height - 80, "Watermolen 1")
    c.drawString(100, height - 95, "6229PM MAASTRICHT")
    c.drawString(100, height - 110, "THE NETHERLANDS")
    
    # Bol.com Reference (Top Center)
    c.setFont("Helvetica", 10)
    c.drawString(width/2 - 50, height - 50, f"bol ref: {order_id}")
    
    # Recipient Information Box with POSTNL header (Central, prominent)
    recipient_box_y = height - 200
    recipient_box_height = 150
    recipient_box_x = 100
    recipient_box_width = width - 200
    
    # Draw recipient box
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(2)
    c.rect(recipient_box_x, recipient_box_y - recipient_box_height, recipient_box_width, recipient_box_height)
    
    # POSTNL Header (prominently displayed)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(recipient_box_x + 10, recipient_box_y - 30, "POSTNL")
    
    # Recipient details (placeholder - in real implementation, get from order data)
    c.setFont("Helvetica", 12)
    c.drawString(recipient_box_x + 10, recipient_box_y - 60, "Recipient Name")
    c.drawString(recipient_box_x + 10, recipient_box_y - 80, "Street Address")
    c.drawString(recipient_box_x + 10, recipient_box_y - 100, "Postal Code & City")
    c.drawString(recipient_box_x + 10, recipient_box_y - 120, "Country")
    
    # Package count
    c.setFont("Helvetica", 10)
    c.drawString(recipient_box_x + recipient_box_width - 80, recipient_box_y - 30, "1 Collo")
    
    # Track & Trace and Barcode section (Bottom)
    bottom_y = recipient_box_y - recipient_box_height - 50
    
    # Use REAL track & trace from Bol.com API if available
    if track_and_trace:
        track_trace_display = track_and_trace
        track_trace_label = "Track & Trace:"
    else:
        # Generate a reference code based on label ID (for tracking purposes)
        track_trace_display = f"3SNNIW{shipping_label_id[:10].replace('-', '')}"
        track_trace_label = "Reference Code:"
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, bottom_y, f"{track_trace_label} {track_trace_display}")
    
    # Carrier information
    c.setFont("Helvetica", 10)
    c.drawString(100, bottom_y - 20, f"Carrier: {carrier_display}")
    
    # Label metadata
    c.setFont("Helvetica", 8)
    c.drawString(100, bottom_y - 40, f"Label ID: {shipping_label_id}")
    c.drawString(100, bottom_y - 55, f"Order ID: {order_id}")
    c.drawString(100, bottom_y - 70, f"Order Item: {order_item_id}")
    c.drawString(100, bottom_y - 85, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Production notice
    if track_and_trace or transporter_code:
        c.setFont("Helvetica", 8)
        c.drawString(100, bottom_y - 100, "✓ PRODUCTION LABEL - Real shipping data from Bol.com API")
    
    # Finish PDF
    c.showPage()
    c.save()
    
    # Get PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data


# Backward compatibility alias (deprecated - use _generate_production_pdf_label instead)
def _generate_mock_pdf_label(shipping_label_id: str, order_item_id: str, order_id: str) -> bytes:
    """Deprecated: Use _generate_production_pdf_label instead"""
    return _generate_production_pdf_label(shipping_label_id, order_item_id, order_id)


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


def _fetch_zpl_label(client: BolAPIClient, order_item_id: str, order_id: str, quantity: int = 1, customer_details: Optional[CustomerDetails] = None) -> str:
    """
    Fetch shipping label following bol.com API v10 flow:
    1. Get delivery options (to get shippingLabelOfferId)
    2. Request shipping label (using shippingLabelOfferId)
    3. Wait for process status to complete
    4. Download PDF shipping label
    5. Save and return label identifier
    
    Returns the label identifier (PDF filename without extension) that is stored in CSV.
    This allows you to match CSV orders to their PDF labels in the label folder.
    
    Example return: "987654321" means the PDF is saved as label/987654321.pdf
    
    Note: Only works for FBR (Fulfilled By Retailer) items.
    
    Args:
        client: Bol.com API client
        order_item_id: Order item ID
        order_id: Order ID for reference
        quantity: Quantity for the order item (default: 1)
        customer_details: Optional customer details
        
    Returns:
        Label identifier matching the PDF filename (without .pdf extension), or empty string if failed
    """
    import base64
    import time as time_module
    
    try:
        logger.info(f"🔍 Starting shipping label flow for order item {order_item_id} (quantity: {quantity})...")
        
        # Step 1: Get delivery options to obtain shippingLabelOfferId
        # According to bol.com API documentation, we need to get delivery options first
        # API endpoint: POST /shipping-labels/delivery-options
        logger.info(f"📋 Step 1: Getting delivery options for order item {order_item_id} (quantity: {quantity})...")
        logger.info(f"   Order ID: {order_id}")
        logger.info(f"   API Endpoint: POST /shipping-labels/delivery-options")
        
        try:
            delivery_options_response = client.get_delivery_options(order_item_id, quantity=quantity)
            
            # Check if response is valid
            if not delivery_options_response:
                logger.error(f"❌ Empty response from get_delivery_options for order item {order_item_id}")
                return ""
            
            # Check for errors in response
            if 'errorMessage' in delivery_options_response:
                error_msg = delivery_options_response.get('errorMessage')
                logger.error(f"❌ API returned error message: {error_msg}")
                return ""
            
            if 'errors' in delivery_options_response:
                errors = delivery_options_response.get('errors', [])
                if errors:
                    logger.error(f"❌ API returned errors: {errors}")
                    return ""
            
            delivery_options = delivery_options_response.get('deliveryOptions', [])
            
            if not delivery_options:
                logger.error(f"❌ No delivery options available for order item {order_item_id}")
                logger.error(f"   Response keys: {list(delivery_options_response.keys())}")
                logger.error(f"   This usually means:")
                logger.error(f"   1. The order item is not FBR (Fulfilled By Retailer)")
                logger.error(f"   2. The orderItemId '{order_item_id}' is invalid")
                logger.error(f"   3. Only FBR items can get shipping labels")
                logger.error(f"   Make sure you're using the orderItemId from orderItems, not the orderId")
                return ""
            
            logger.info(f"✅ Found {len(delivery_options)} delivery option(s)")
            
            # Log all available options for debugging
            for idx, option in enumerate(delivery_options):
                option_id = option.get('shippingLabelOfferId', 'N/A')
                label_name = option.get('labelDisplayName', 'N/A')
                transporter = option.get('transporterCode', 'N/A')
                logger.info(f"   Option {idx + 1}: {label_name} (ID: {option_id}, Transporter: {transporter})")
            
            # Look for "verzenden via bol" offer (preferred)
            shipping_label_offer_id = None
            for option in delivery_options:
                label_display_name = option.get('labelDisplayName', '').lower()
                if 'verzenden via bol' in label_display_name or 'bol' in label_display_name:
                    shipping_label_offer_id = option.get('shippingLabelOfferId')
                    logger.info(f"✅ Found 'verzenden via bol' offer: {shipping_label_offer_id}")
                    break
            
            # If not found, use first available offer
            if not shipping_label_offer_id and delivery_options:
                shipping_label_offer_id = delivery_options[0].get('shippingLabelOfferId')
                label_name = delivery_options[0].get('labelDisplayName', 'Unknown')
                logger.info(f"⚠️ 'verzenden via bol' not found, using first available offer: {shipping_label_offer_id} ({label_name})")
            
            if not shipping_label_offer_id:
                logger.error(f"❌ No shippingLabelOfferId found in delivery options")
                logger.error(f"   Available options: {delivery_options}")
                return ""
                
        except Exception as delivery_error:
            error_str = str(delivery_error)
            logger.error(f"❌ Failed to get delivery options for order item {order_item_id}: {delivery_error}")
            logger.error(f"   Error type: {type(delivery_error).__name__}")
            if "404" in error_str or "Not Found" in error_str:
                logger.error(f"   This usually means the order item is not FBR (Fulfilled By Retailer)")
                logger.error(f"   Only FBR items can get shipping labels")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            return ""
        
        # Step 2: Request shipping label using shippingLabelOfferId
        logger.info(f"📋 Step 2: Creating shipping label for order item {order_item_id} with offer ID {shipping_label_offer_id}...")
        try:
            label_response = client.create_shipping_label(
                order_item_id, 
                shipping_label_offer_id=shipping_label_offer_id,
                quantity=quantity
            )
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
        
        # Log response structure for debugging
        logger.info(f"📦 Create shipping label response keys: {list(label_response.keys())}")
        
        # Step 3: Extract processStatusId from response
        # According to bol.com API v10, the response contains processStatusId for async processing
        process_status_id = None
        shipping_label_id = None
        
        # Try direct processStatusId (most common)
        if 'processStatusId' in label_response:
            process_status_id = label_response.get('processStatusId')
            logger.info(f"✅ Found processStatusId: {process_status_id}")
        
        # Try nested processStatus.processStatusId
        if not process_status_id and 'processStatus' in label_response:
            process_status = label_response.get('processStatus', {})
            process_status_id = process_status.get('processStatusId')
            entity_id = process_status.get('entityId')  # This would be shippingLabelId if available immediately
            if entity_id:
                shipping_label_id = entity_id
                logger.info(f"✅ Found shippingLabelId directly in processStatus: {shipping_label_id}")
        
        if not process_status_id:
            logger.error(f"❌ No processStatusId found in label response for order item {order_item_id}")
            logger.error(f"Response keys: {list(label_response.keys())}")
            logger.error(f"Response (first 1000 chars): {str(label_response)[:1000]}")
            return ""
        
        # Step 4: Wait for async process to complete and get shippingLabelId
        if not shipping_label_id:
            logger.info(f"📋 Step 3: Waiting for async process {process_status_id} to complete...")
            max_status_checks = 15  # Increased to allow more time for label generation
            check_interval = 2  # Wait 2 seconds between checks
            
            for status_check in range(max_status_checks):
                if status_check > 0:
                    time_module.sleep(check_interval)
                
                try:
                    status_response = client.get_process_status(process_status_id)
                    status = status_response.get('status', '').upper()
                    logger.info(f"   Process status check {status_check + 1}/{max_status_checks}: {status}")
                    
                    if status == 'SUCCESS':
                        # Get entityId which is the shippingLabelId
                        shipping_label_id = status_response.get('entityId')
                        if shipping_label_id:
                            logger.info(f"✅ Process completed successfully, shippingLabelId: {shipping_label_id}")
                            break
                        else:
                            logger.warning(f"⚠️ Process status is SUCCESS but no entityId found")
                            logger.warning(f"   Response keys: {list(status_response.keys())}")
                            # Continue checking - entityId might appear later
                            
                    elif status in ['FAILURE', 'TIMEOUT', 'CANCELLED']:
                        logger.error(f"❌ Process failed with status: {status}")
                        error_message = status_response.get('errorMessage', 'Unknown error')
                        logger.error(f"   Error message: {error_message}")
                        return ""
                    elif status == 'PENDING':
                        logger.info(f"   Process still pending, will check again...")
                    else:
                        logger.info(f"   Process status: {status}, will check again...")
                        
                except Exception as status_error:
                    logger.warning(f"⚠️ Error checking process status (attempt {status_check + 1}): {status_error}")
                    if status_check < max_status_checks - 1:
                        continue
                    else:
                        logger.error(f"❌ Failed to check process status after {max_status_checks} attempts")
                        return ""
            
            if not shipping_label_id:
                logger.error(f"❌ Could not get shippingLabelId from process status after {max_status_checks} checks")
                return ""
        
        # Step 5: Download PDF shipping label from Bol.com API
        logger.info(f"📋 Step 4: Downloading PDF shipping label {shipping_label_id} from Bol.com API...")
        logger.info(f"   Using endpoint: GET /retailer/shipping-labels/{shipping_label_id}")
        logger.info(f"   Accept header: application/pdf")
        
        # Wait a bit for the label to be ready (Bol.com may need time to generate it)
        logger.info(f"⏳ Waiting 3 seconds for Bol.com to generate the label...")
        time_module.sleep(3)
        
        # Try to download the PDF label with retries
        max_retries = 10  # Increased retries
        wait_between_retries = [2, 3, 5, 5, 10, 10, 15, 15, 20]  # Progressive wait times
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = wait_between_retries[min(attempt - 1, len(wait_between_retries) - 1)]
                    logger.info(f"⏳ Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                    time_module.sleep(wait_time)
                    logger.info(f"🔄 Retry {attempt + 1}/{max_retries}: Downloading PDF from Bol.com API...")
                else:
                    logger.info(f"📥 Attempt {attempt + 1}/{max_retries}: Downloading PDF from Bol.com API...")
                
                # Fetch PDF label from Bol.com API
                label_response = client.get_shipping_label(shipping_label_id, label_format="PDF")
                pdf_data = label_response.get('data', None)
                content_type = label_response.get('content_type', '')
                track_and_trace = label_response.get('track_and_trace', '')
                transporter_code = label_response.get('transporter_code', '')
                
                logger.info(f"📥 Response - Content-Type: {content_type}, Data type: {type(pdf_data)}")
                if track_and_trace:
                    logger.info(f"   Track & Trace: {track_and_trace}")
                if transporter_code:
                    logger.info(f"   Transporter: {transporter_code}")
                
                # Check if we got PDF data
                if pdf_data:
                    # Handle binary PDF data
                    if isinstance(pdf_data, bytes):
                        pdf_bytes = pdf_data
                    elif isinstance(pdf_data, str):
                        # Might be base64 encoded
                        try:
                            pdf_bytes = base64.b64decode(pdf_data)
                        except Exception as decode_error:
                            logger.warning(f"⚠️ PDF data is string but not base64: {decode_error}")
                            # Try to encode as UTF-8 (unlikely to work for PDF, but try)
                            pdf_bytes = pdf_data.encode('utf-8')
                    else:
                        logger.warning(f"⚠️ Unexpected PDF data type: {type(pdf_data)}")
                        if attempt < max_retries - 1:
                            continue
                        else:
                            break
                    
                    # Validate it's actually a PDF
                    if len(pdf_bytes) >= 4 and pdf_bytes[:4] == b'%PDF':
                        # This is a valid PDF - save it
                        label_id = _save_pdf_label(pdf_bytes, shipping_label_id)
                        logger.info(f"✅ Successfully downloaded and saved PDF label: {label_id}.pdf ({len(pdf_bytes)} bytes)")
                        logger.info(f"   Track & Trace: {track_and_trace or 'N/A'}")
                        logger.info(f"   Transporter: {transporter_code or 'N/A'}")
                        return label_id
                    else:
                        logger.warning(f"⚠️ Downloaded data doesn't appear to be a PDF (attempt {attempt + 1}/{max_retries})")
                        logger.warning(f"   First 20 bytes (hex): {pdf_bytes[:20].hex() if len(pdf_bytes) >= 20 else 'too short'}")
                        logger.warning(f"   Data length: {len(pdf_bytes)} bytes")
                        if attempt < max_retries - 1:
                            continue
                
                logger.info(f"   No valid PDF data in response yet (attempt {attempt + 1}/{max_retries})")
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"⚠️ Attempt {attempt + 1}/{max_retries} failed: {error_msg}")
                
                # Check for specific HTTP errors
                if "404" in error_msg:
                    logger.warning(f"   Label not found (404) - may need more time to be generated")
                    if attempt < max_retries - 1:
                        continue
                elif "406" in error_msg:
                    logger.warning(f"   Not Acceptable (406) - Accept header issue")
                    if attempt < max_retries - 1:
                        continue
                elif "400" in error_msg:
                    logger.warning(f"   Bad Request (400) - check shipping label ID")
                    if attempt < max_retries - 1:
                        continue
                else:
                    if attempt < max_retries - 1:
                        continue
        
        # If we reach here, we failed to download the PDF
        logger.error(f"❌ Could not download PDF label from Bol.com API after {max_retries} attempts")
        logger.error(f"   Shipping Label ID: {shipping_label_id}")
        logger.error(f"   Order Item ID: {order_item_id}")
        logger.error(f"   Order ID: {order_id}")
        logger.error(f"")
        logger.error(f"   Please check:")
        logger.error(f"      1. Shipping label was created successfully")
        logger.error(f"      2. Process status completed successfully")
        logger.error(f"      3. Label is available in Bol.com system")
        logger.error(f"      4. API credentials have correct permissions")
        logger.error(f"      5. Network connectivity to Bol.com API")
        return ""
        
    except Exception as e:
        logger.error(f"❌ Exception while fetching shipping label for order item {order_item_id}: {e}")
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
    pdf_generation_count = 0
    pdf_failure_count = 0
    
    for order in orders:
        order_time_str = (
            order.order_placed_date_time.strftime("%Y-%m-%d %H:%M:%S")
            if order.order_placed_date_time
            else ""
        )
        for item in order.order_items:
            # Fetch shipping label if client is provided
            # According to bol.com API, we need to:
            # 1. Get delivery options (to get shippingLabelOfferId)
            # 2. Create shipping label
            # 3. Wait for process status
            # 4. Download PDF
            tracking_label = ""
            if client:
                fulfilment_method = item.fulfilment_method or ""
                is_fbr = fulfilment_method.upper() == "FBR"
                
                logger.info(f"📋 Processing order item {item.order_item_id} (EAN: {item.ean}, Quantity: {item.quantity}, Fulfilment: {fulfilment_method or 'Unknown'})")
                
                # Check if item is explicitly not FBR
                if fulfilment_method and not is_fbr:
                    logger.warning(f"⚠️ Order item {item.order_item_id} is not FBR (fulfilment method: {fulfilment_method})")
                    logger.warning(f"   Shipping labels are only available for FBR items. Skipping label fetch.")
                    tracking_label = ""  # Leave empty for non-FBR items
                else:
                    # For FBR items or unknown fulfilment, attempt to fetch shipping label
                    # The _fetch_zpl_label function will handle:
                    # - Getting delivery options (which confirms FBR status)
                    # - Creating the shipping label
                    # - Downloading the PDF
                    if is_fbr:
                        logger.info(f"✅ Order item {item.order_item_id} is FBR - proceeding to fetch shipping label")
                    else:
                        logger.info(f"⚠️ Fulfilment method unknown for order item {item.order_item_id}")
                        logger.info(f"   Will attempt to fetch shipping label (will fail if not FBR)")
                    
                    try:
                        tracking_label = _fetch_zpl_label(
                            client, 
                            item.order_item_id, 
                            order.order_id, 
                            quantity=item.quantity, 
                            customer_details=order.customer_details
                        )
                        
                        if tracking_label:
                            # Verify PDF was actually created
                            pdf_path = os.path.join(LABEL_DIR, f"{tracking_label}.pdf")
                            if os.path.exists(pdf_path):
                                logger.info(f"✅ Successfully fetched and verified label for order item {item.order_item_id}: {tracking_label}")
                                pdf_generation_count += 1
                            else:
                                logger.warning(f"⚠️ Label ID returned ({tracking_label}) but PDF not found at {pdf_path}")
                                logger.warning(f"   This should not happen - PDF should always be generated")
                                pdf_failure_count += 1
                        else:
                            logger.warning(f"⚠️ No shipping label returned for order item {item.order_item_id}")
                            logger.warning(f"   Shipping Label column will be empty in CSV")
                            pdf_failure_count += 1
                            
                    except Exception as label_fetch_error:
                        logger.error(f"❌ Exception while fetching label for order item {item.order_item_id}: {label_fetch_error}")
                        import traceback
                        logger.error(traceback.format_exc())
                        tracking_label = ""  # Set to empty on error
                        pdf_failure_count += 1
            
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
    
    # Log PDF generation summary
    total_items = sum(len(order.order_items) for order in orders)
    logger.info("")
    logger.info("="*80)
    logger.info(f"PDF Generation Summary for {category} batch {batch_number}:")
    logger.info(f"  Total order items processed: {total_items}")
    logger.info(f"  PDFs successfully generated: {pdf_generation_count}")
    logger.info(f"  PDFs failed/missing: {pdf_failure_count}")
    logger.info("="*80)
    
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
    batch_dir = _batch_dir()
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

    # Try to get SFTP credentials from system_config.json first, fallback to config.py
    sftp_host = SFTP_HOST
    sftp_port = SFTP_PORT
    sftp_username = SFTP_USERNAME
    sftp_password = SFTP_PASSWORD
    sftp_remote_dir = SFTP_REMOTE_BATCH_DIR
    
    try:
        from config_manager import load_config
        config = load_config()
        if 'ftp' in config:
            ftp_config = config['ftp']
            sftp_host = ftp_config.get('host', SFTP_HOST)
            sftp_port = ftp_config.get('port', SFTP_PORT)
            sftp_username = ftp_config.get('username', SFTP_USERNAME)
            sftp_password = ftp_config.get('password', SFTP_PASSWORD)
            sftp_remote_dir = ftp_config.get('remote_batch_dir', SFTP_REMOTE_BATCH_DIR)
            logger.info("✅ Usando credenciais SFTP do system_config.json")
    except Exception as config_error:
        logger.warning(f"⚠️  Não foi possível carregar credenciais do system_config.json: {config_error}")
        logger.info("📋 Usando credenciais do config.py")

    logger.info("="*80)
    logger.info("📤 Iniciando upload de arquivos CSV para SFTP")
    logger.info(f"Servidor: {sftp_host}:{sftp_port}")
    logger.info(f"Usuário: {sftp_username}")
    logger.info(f"Diretório remoto: {sftp_remote_dir}")
    logger.info(f"Total de arquivos: {len(file_paths)}")
    for i, file_path in enumerate(file_paths, 1):
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            logger.info(f"  {i}. {os.path.basename(file_path)} ({file_size} bytes)")
        else:
            logger.warning(f"  {i}. {os.path.basename(file_path)} (⚠️  ARQUIVO NÃO ENCONTRADO)")
    logger.info("="*80)

    transport = None
    uploaded_count = 0
    failed_count = 0
    skipped_count = 0
    
    try:
        transport = paramiko.Transport((sftp_host, sftp_port))
        transport.banner_timeout = 30  # Increase banner timeout
        transport.auth_timeout = 30    # Increase auth timeout
        
        # Try connection with credentials
        logger.info("🔐 Tentando autenticação SFTP...")
        transport.connect(username=sftp_username, password=sftp_password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        logger.info("✅ Conectado ao servidor SFTP: %s:%d", sftp_host, sftp_port)

        # Ensure remote directory exists (best-effort)
        try:
            sftp.chdir(sftp_remote_dir)
            logger.info("✅ Diretório remoto existe: %s", sftp_remote_dir)
        except IOError as dir_error:
            # Try to create directories recursively
            logger.info("⚠️  Diretório remoto não encontrado, tentando criar: %s", sftp_remote_dir)
            logger.info("Erro: %s", dir_error)
            parts = [p for p in sftp_remote_dir.strip("/").split("/") if p]
            current = ""
            for part in parts:
                current = f"{current}/{part}" if current else f"/{part}"
                try:
                    sftp.chdir(current)
                    logger.debug("Diretório já existe: %s", current)
                except IOError:
                    try:
                        sftp.mkdir(current)
                        sftp.chdir(current)
                        logger.info("✅ Criado diretório: %s", current)
                    except Exception as mkdir_error:
                        logger.error("❌ Erro ao criar diretório %s: %s", current, mkdir_error)
                        raise

        # List CSV files in remote directory (no subdirectories)
        existing_remote_files: Dict[str, int] = {}
        try:
            items = sftp.listdir(sftp_remote_dir)
            for item in items:
                item_path = os.path.join(sftp_remote_dir, item).replace("\\", "/")
                try:
                    stat = sftp.stat(item_path)
                    if not (stat.st_mode & 0o040000):  # Not a directory
                        if item.lower().endswith(".csv"):
                            existing_remote_files[item.lower()] = int(stat.st_size)
                except Exception:
                    pass
            logger.info("📋 Encontrados %d CSV(s) já existentes no servidor", len(existing_remote_files))
        except Exception as list_error:
            logger.warning("⚠️  Não foi possível listar arquivos remotos em %s: %s", sftp_remote_dir, list_error)
            existing_remote_files = {}

        # Upload each file directly (no subdirectories)
        for local_path in file_paths:
            if not os.path.exists(local_path):
                logger.error("❌ Arquivo local não encontrado: %s", local_path)
                failed_count += 1
                continue
            
            # Get just the filename (no subdirectories)
            filename = os.path.basename(local_path)
            
            # Build remote path (directly in remote_dir, no subdirectories)
            remote_path = os.path.join(sftp_remote_dir, filename).replace("\\", "/")
            
            filename_lower = filename.lower()
            
            try:
                local_size = os.path.getsize(local_path)

                # Skip upload if it already exists on server (idempotent)
                existing_size = existing_remote_files.get(filename_lower)
                if existing_size is not None:
                    # If we know the size and it matches, skip
                    if existing_size == local_size or existing_size == -1:
                        logger.info("⏭️  CSV já existe no servidor, pulando upload: %s (local=%d bytes, remoto=%s)",
                                    filename, local_size, "desconhecido" if existing_size == -1 else str(existing_size))
                        skipped_count += 1
                        continue
                    else:
                        logger.warning("⚠️  CSV já existe no servidor com tamanho diferente; NÃO será sobrescrito: %s (local=%d, remoto=%d)",
                                       filename, local_size, existing_size)
                        skipped_count += 1
                        continue

                logger.info("📤 Enviando %s (%d bytes) para %s", filename, local_size, remote_path)
                sftp.put(local_path, remote_path)
                
                # Verify upload by checking file exists and size matches
                try:
                    remote_stat = sftp.stat(remote_path)
                    if remote_stat.st_size == local_size:
                        logger.info("✅ Upload bem-sucedido: %s (%d bytes)", filename, local_size)
                        uploaded_count += 1
                        existing_remote_files[filename_lower] = local_size
                    else:
                        logger.warning(
                            "⚠️  Tamanho diferente após upload: %s (local=%d, remoto=%d)",
                            filename, local_size, remote_stat.st_size
                        )
                        uploaded_count += 1  # Still count as uploaded
                        existing_remote_files[filename_lower] = int(remote_stat.st_size)
                except Exception as verify_error:
                    logger.warning("⚠️  Não foi possível verificar upload de %s: %s", relative_path, verify_error)
                    logger.warning("   Assumindo que o upload foi bem-sucedido")
                    uploaded_count += 1  # Assume uploaded if we can't verify
                    existing_remote_files[relative_path_lower] = -1
                    
            except Exception as upload_error:
                logger.error("❌ Falha no upload de %s: %s", relative_path, upload_error)
                logger.error("   Tipo de erro: %s", type(upload_error).__name__)
                logger.error("   Caminho local: %s", local_path)
                logger.error("   Caminho remoto: %s", remote_path)
                import traceback
                logger.error("   Traceback completo: %s", traceback.format_exc())
                failed_count += 1
                
    except paramiko.AuthenticationException as auth_error:
        logger.error("❌ Erro de autenticação SFTP: %s", auth_error)
        logger.error("   Verifique as credenciais em config.py")
        failed_count = len(file_paths)
    except paramiko.SSHException as ssh_error:
        logger.error("❌ Erro de conexão SSH/SFTP: %s", ssh_error)
        failed_count = len(file_paths)
    except Exception as e:
        logger.error("❌ Erro de conexão/upload SFTP: %s", e)
        logger.error("   Tipo de erro: %s", type(e).__name__)
        import traceback
        logger.error("Traceback completo: %s", traceback.format_exc())
        failed_count = len(file_paths)
    finally:
        if transport:
            try:
                transport.close()
            except:
                pass
        logger.info("="*80)
        logger.info(
            "📊 Upload concluído: %d enviados, %d pulados (já existiam), %d falhas de %d total",
            uploaded_count, skipped_count, failed_count, len(file_paths)
        )
        logger.info("="*80)
        
        if failed_count > 0:
            logger.warning("⚠️  Alguns arquivos falharam no upload. Verifique os logs acima.")


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
    """
    Run one full processing cycle for all active accounts.
    Processes both Jean and Trivium accounts if configured.
    """
    logger.info("Starting Bol.com order processing run...")
    
    # Try to use multi-account processor if available
    try:
        from config_manager import get_active_bol_accounts
        from multi_account_processor import process_all_accounts
        
        active_accounts = get_active_bol_accounts()
        
        if active_accounts and len(active_accounts) > 0:
            logger.info(f"📋 Encontradas {len(active_accounts)} conta(s) ativa(s): {[acc['name'] for acc in active_accounts]}")
            logger.info("🔄 Processando todas as contas ativas...")
            
            # Use multi-account processor
            result = process_all_accounts()
            
            logger.info("="*80)
            logger.info("✅ Processamento concluído para todas as contas")
            logger.info(f"   Contas processadas: {result.get('accounts_processed', 0)}")
            logger.info(f"   Total de pedidos processados: {result.get('total_orders', 0)}")
            logger.info("="*80)
            
            # Log results for each account
            for account_result in result.get('results', []):
                account_name = account_result.get('account', 'Unknown')
                processed = account_result.get('processed', 0)
                success = account_result.get('success', False)
                status = "✅" if success else "❌"
                logger.info(f"   {status} {account_name}: {processed} pedido(s) processado(s)")
            
            return
        
    except ImportError as import_error:
        logger.warning(f"⚠️  Multi-account processor não disponível: {import_error}")
        logger.info("📋 Processando com conta única do config.py...")
    except Exception as multi_error:
        logger.warning(f"⚠️  Erro ao processar múltiplas contas: {multi_error}")
        logger.info("📋 Fallback: Processando com conta única do config.py...")
    
    # Fallback to single account processing (original behavior)
    logger.info("Processando com conta única (Jean)...")
    
    # Initialize database
    init_database()

    # PRODUCTION MODE: Always use test_mode=False for live labels
    client = BolAPIClient(BOL_CLIENT_ID, BOL_CLIENT_SECRET, test_mode=False)
    
    # Fetch orders - get list first, then fetch individual orders for complete details
    logger.info("📋 Fetching list of open orders...")
    raw_orders_list = client.get_all_open_orders()
    
    if not raw_orders_list:
        logger.info("No open orders to process.")
        return
    
    logger.info(f"📋 Found {len(raw_orders_list)} open order(s), fetching individual order details...")
    
    # Fetch individual orders to get complete order item information
    # According to bol.com API, get_order() returns full order details with all order items
    all_orders = []
    for order_summary in raw_orders_list:
        order_id = order_summary.get('orderId')
        if not order_id:
            logger.warning(f"⚠️ Order summary missing orderId, skipping: {order_summary}")
            continue
        
        try:
            # Fetch individual order for complete details
            full_order_data = client.get_order(order_id)
            order = Order.from_dict(full_order_data)
            all_orders.append(order)
            logger.debug(f"✅ Fetched full details for order {order_id} ({len(order.order_items)} item(s))")
        except Exception as fetch_error:
            logger.error(f"❌ Failed to fetch order {order_id}: {fetch_error}")
            # Fallback: try to use summary data if available
            try:
                order = Order.from_dict(order_summary)
                all_orders.append(order)
                logger.warning(f"⚠️ Using summary data for order {order_id} (some details may be missing)")
            except Exception as fallback_error:
                logger.error(f"❌ Failed to parse order summary for {order_id}: {fallback_error}")
                continue

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
        
        # Upload label PDFs to SFTP (only PDFs referenced in the generated CSV files)
        if LABEL_UPLOADER_AVAILABLE and upload_labels_for_csv_files:
            try:
                logger.info("📤 Uploading label PDFs to SFTP (from generated CSV files)...")
                upload_labels_for_csv_files(files_created)
                logger.info("✅ Label PDF upload completed")
            except Exception as label_error:
                logger.error(f"❌ Failed to upload label PDFs: {label_error}")
                import traceback
                logger.error(traceback.format_exc())
                logger.error("   Labels are saved locally in 'label/' folder")
                # Try fallback: upload all labels
                try:
                    logger.info("🔄 Tentando upload de todos os labels como fallback...")
                    upload_all_labels()
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback upload também falhou: {fallback_error}")
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


def run_continuous() -> None:
    """
    Run processing continuously without time checking.
    Processes orders every PROCESS_INTERVAL seconds.
    Perfect for server deployment - runs 24/7 checking for new orders.
    """
    logger.info("="*80)
    logger.info("🚀 Modo Contínuo de Processamento")
    logger.info("="*80)
    logger.info(f"Intervalo de verificação: {PROCESS_INTERVAL} segundos ({PROCESS_INTERVAL/60:.1f} minutos)")
    logger.info("O processamento rodará continuamente, verificando novos pedidos a cada intervalo")
    logger.info("Pressione Ctrl+C para parar")
    logger.info("="*80)
    logger.info("")

    run_count = 0
    
    try:
        while True:
            run_count += 1
            logger.info("")
            logger.info("="*80)
            logger.info(f"🔄 Execução #{run_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*80)
            
            try:
                run_processing_once()
            except Exception as e:
                logger.error(f"❌ Erro durante processamento: {e}")
                logger.error(f"   Tipo de erro: {type(e).__name__}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                logger.warning("⚠️  Continuando após erro...")
            
            logger.info("")
            logger.info(f"⏳ Aguardando {PROCESS_INTERVAL} segundos até próxima verificação...")
            logger.info("")
            
            # Sleep for the configured interval
            time_module.sleep(PROCESS_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("")
        logger.info("="*80)
        logger.info("🛑 Processamento contínuo interrompido pelo usuário")
        logger.info(f"Total de execuções: {run_count}")
        logger.info("="*80)


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
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == "--once" or arg == "-o":
            # Run a single processing cycle
            logger.info("Executando um único ciclo de processamento...")
            run_processing_once()
        elif arg == "--scheduler" or arg == "-s":
            # Run as time-based scheduler (checks specific times)
            logger.info("Iniciando modo scheduler baseado em horários (pressione Ctrl+C para parar)...")
            run_scheduler()
        elif arg == "--continuous" or arg == "-c":
            # Run continuously (default for server)
            run_continuous()
        elif arg == "--help" or arg == "-h":
            print("Uso: python3 order_processing.py [opção]")
            print("")
            print("Opções:")
            print("  (sem opção)  - Modo contínuo (padrão para servidor)")
            print("  --continuous, -c  - Modo contínuo (verifica a cada intervalo)")
            print("  --once, -o   - Executa uma única vez")
            print("  --scheduler, -s  - Modo scheduler baseado em horários")
            print("  --help, -h   - Mostra esta ajuda")
            sys.exit(0)
        else:
            logger.error(f"Opção desconhecida: {arg}")
            logger.info("Use --help para ver opções disponíveis")
            sys.exit(1)
    else:
        # Default: Run continuously (best for server deployment)
        run_continuous()


