"""
Example: Integration of Label Uploader with Order Processing

This shows how to integrate the label uploader with your existing order processing workflow.
"""

import os
from label_uploader import upload_label_pdf_to_ftp, LOCAL_LABEL_DIR

def save_and_upload_label(label_pdf_content: bytes, order_id: str) -> bool:
    """
    Save a shipping label PDF and automatically upload it to FTP.
    
    Args:
        label_pdf_content: The PDF content as bytes
        order_id: The order ID to use for the filename
        
    Returns:
        bool: True if saved and uploaded successfully
    """
    # Create label directory if it doesn't exist
    os.makedirs(LOCAL_LABEL_DIR, exist_ok=True)
    
    # Generate filename
    filename = f"{order_id}.pdf"
    local_path = os.path.join(LOCAL_LABEL_DIR, filename)
    
    try:
        # Save the PDF locally
        with open(local_path, 'wb') as f:
            f.write(label_pdf_content)
        print(f"✅ Saved label: {filename}")
        
        # Upload to FTP
        if upload_label_pdf_to_ftp(local_path):
            print(f"✅ Uploaded label to FTP: {filename}")
            return True
        else:
            print(f"⚠️  Label saved locally but upload failed: {filename}")
            return False
            
    except Exception as e:
        print(f"❌ Error saving/uploading label {filename}: {e}")
        return False


def process_order_with_label(order_data: dict):
    """
    Example: Process an order and handle its shipping label.
    
    This is a simplified example showing how to integrate label upload
    into your order processing workflow.
    """
    order_id = order_data.get('orderId')
    
    print(f"\n📦 Processing order: {order_id}")
    
    # Your existing order processing logic here...
    # For example:
    # - Validate order
    # - Generate Excel batch
    # - etc.
    
    # If you have shipping label data (e.g., from Bol.com API)
    label_data = order_data.get('shippingLabelPdf')  # This would be your actual label data
    
    if label_data:
        print(f"📄 Shipping label found for order {order_id}")
        
        # Save and upload the label
        if save_and_upload_label(label_data, order_id):
            print(f"✅ Label processed successfully for order {order_id}")
        else:
            print(f"⚠️  Label processing incomplete for order {order_id}")
    else:
        print(f"ℹ️  No shipping label for order {order_id}")


# Example usage patterns:

def example_1_manual_upload():
    """Example 1: Manually upload a specific label file"""
    order_id = "0437fe94-fce1-452c-a294-53d2e7f6ec09"
    local_path = os.path.join(LOCAL_LABEL_DIR, f"{order_id}.pdf")
    
    if os.path.exists(local_path):
        success = upload_label_pdf_to_ftp(local_path)
        if success:
            print(f"✅ Successfully uploaded label for order {order_id}")
    else:
        print(f"❌ Label file not found: {local_path}")


def example_2_batch_process_orders():
    """Example 2: Process multiple orders with labels"""
    orders = [
        {'orderId': 'order-123', 'shippingLabelPdf': b'...pdf content...'},
        {'orderId': 'order-456', 'shippingLabelPdf': b'...pdf content...'},
        {'orderId': 'order-789', 'shippingLabelPdf': None},
    ]
    
    for order in orders:
        process_order_with_label(order)


def example_3_with_background_monitor():
    """
    Example 3: Use with background monitor
    
    Instead of uploading immediately, you can:
    1. Save labels to the 'label' folder
    2. Let the background monitor (run_label_monitor.py) handle uploads
    
    This is useful when you want to decouple label generation from upload.
    """
    order_id = "order-999"
    label_content = b'...pdf content...'
    
    # Just save the label
    os.makedirs(LOCAL_LABEL_DIR, exist_ok=True)
    local_path = os.path.join(LOCAL_LABEL_DIR, f"{order_id}.pdf")
    
    with open(local_path, 'wb') as f:
        f.write(label_content)
    
    print(f"✅ Label saved: {order_id}.pdf")
    print("ℹ️  Background monitor will upload it automatically")


if __name__ == "__main__":
    print("="*80)
    print("LABEL UPLOADER INTEGRATION EXAMPLES")
    print("="*80)
    print("\nThis file contains examples of how to integrate the label uploader")
    print("with your order processing workflow.")
    print("\nSee the function definitions for different usage patterns:")
    print("  - example_1_manual_upload()")
    print("  - example_2_batch_process_orders()")
    print("  - example_3_with_background_monitor()")
    print("\nTo use in your code:")
    print("  from label_uploader import upload_label_pdf_to_ftp")
    print("="*80)

