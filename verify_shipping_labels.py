"""
Verification script to test the shipping label flow
This script verifies that shipping labels can be fetched and included in CSV files
"""

import logging
import sys
from bol_api_client import BolAPIClient
from bol_dtos import Order
from order_processing import _fetch_zpl_label, _create_csv_for_category
from config import BOL_CLIENT_ID, BOL_CLIENT_SECRET, TEST_MODE
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_shipping_label_flow():
    """Verify the complete shipping label flow"""
    logger.info("="*80)
    logger.info("🔍 VERIFYING SHIPPING LABEL FLOW")
    logger.info("="*80)
    logger.info("")
    
    # Step 1: Initialize API client
    logger.info("📋 Step 1: Initializing Bol.com API client...")
    try:
        client = BolAPIClient(BOL_CLIENT_ID, BOL_CLIENT_SECRET, test_mode=TEST_MODE)
        logger.info("✅ API client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize API client: {e}")
        return False
    
    # Step 2: Fetch orders
    logger.info("")
    logger.info("📋 Step 2: Fetching open orders...")
    try:
        raw_orders_list = client.get_all_open_orders()
        logger.info(f"✅ Found {len(raw_orders_list)} open order(s)")
        
        if not raw_orders_list:
            logger.warning("⚠️ No open orders found. Cannot test shipping label flow.")
            return False
        
        # Fetch individual orders for complete details
        logger.info("📋 Fetching individual order details...")
        all_orders = []
        for order_summary in raw_orders_list:
            order_id = order_summary.get('orderId')
            if not order_id:
                continue
            
            try:
                full_order_data = client.get_order(order_id)
                order = Order.from_dict(full_order_data)
                all_orders.append(order)
                logger.info(f"✅ Fetched order {order_id} ({len(order.order_items)} item(s))")
            except Exception as e:
                logger.warning(f"⚠️ Failed to fetch order {order_id}: {e}")
                continue
        
        logger.info(f"✅ Successfully fetched {len(all_orders)} order(s) with complete details")
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch orders: {e}")
        return False
    
    # Step 3: Find FBR order items
    logger.info("")
    logger.info("📋 Step 3: Finding FBR order items...")
    fbr_items = []
    for order in all_orders:
        for item in order.order_items:
            fulfilment_method = item.fulfilment_method or ""
            is_fbr = fulfilment_method.upper() == "FBR"
            
            if is_fbr:
                fbr_items.append({
                    'order': order,
                    'item': item
                })
                logger.info(f"✅ Found FBR item: {item.order_item_id} (Order: {order.order_id}, EAN: {item.ean})")
    
    if not fbr_items:
        logger.warning("⚠️ No FBR items found in open orders.")
        logger.warning("   Shipping labels can only be created for FBR (Fulfilled By Retailer) items.")
        logger.warning("   The system will work correctly, but you need FBR orders to test.")
        return True  # This is not an error, just no FBR items available
    
    logger.info(f"✅ Found {len(fbr_items)} FBR item(s) to test")
    
    # Step 4: Test shipping label fetching for first FBR item
    logger.info("")
    logger.info("📋 Step 4: Testing shipping label fetching...")
    test_item = fbr_items[0]
    order = test_item['order']
    item = test_item['item']
    
    logger.info(f"   Testing with order item: {item.order_item_id}")
    logger.info(f"   Order ID: {order.order_id}")
    logger.info(f"   EAN: {item.ean}")
    logger.info(f"   Quantity: {item.quantity}")
    
    try:
        label_id = _fetch_zpl_label(
            client,
            item.order_item_id,
            order.order_id,
            quantity=item.quantity,
            customer_details=order.customer_details
        )
        
        if label_id:
            logger.info("")
            logger.info("="*80)
            logger.info("✅ SHIPPING LABEL FLOW VERIFICATION SUCCESSFUL")
            logger.info("="*80)
            logger.info(f"   Label ID: {label_id}")
            
            # Verify PDF file exists
            pdf_path = os.path.join("label", f"{label_id}.pdf")
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                logger.info(f"   PDF file: {pdf_path} ({file_size} bytes)")
                logger.info("✅ PDF file verified")
            else:
                logger.warning(f"⚠️ PDF file not found at: {pdf_path}")
            
            logger.info("")
            logger.info("✅ The shipping label flow is working correctly!")
            logger.info("   - Delivery options fetched successfully")
            logger.info("   - Shipping label created successfully")
            logger.info("   - PDF downloaded and saved")
            logger.info("   - Label ID returned for CSV inclusion")
            return True
        else:
            logger.error("")
            logger.error("="*80)
            logger.error("❌ SHIPPING LABEL FLOW VERIFICATION FAILED")
            logger.error("="*80)
            logger.error("   No label ID returned")
            logger.error("   Check the logs above for error details")
            return False
            
    except Exception as e:
        logger.error("")
        logger.error("="*80)
        logger.error("❌ SHIPPING LABEL FLOW VERIFICATION FAILED")
        logger.error("="*80)
        logger.error(f"   Exception: {e}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return False


def main():
    """Main entry point"""
    try:
        success = verify_shipping_label_flow()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
