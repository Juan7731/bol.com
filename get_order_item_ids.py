"""
Script to get order item IDs from orders
Use this to find the correct orderItemId to test with
"""

import logging
import sys
from bol_api_client import BolAPIClient
from bol_dtos import Order
from config import BOL_CLIENT_ID, BOL_CLIENT_SECRET, TEST_MODE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_order_item_ids():
    """Get all order item IDs from open orders"""
    logger.info("="*80)
    logger.info("FETCHING ORDER ITEM IDs FROM OPEN ORDERS")
    logger.info("="*80)
    
    client = BolAPIClient(BOL_CLIENT_ID, BOL_CLIENT_SECRET, test_mode=TEST_MODE)
    
    try:
        raw_orders = client.get_all_open_orders()
        all_orders = [Order.from_dict(o) for o in raw_orders]
        
        logger.info(f"\nFound {len(all_orders)} open orders\n")
        
        for order in all_orders:
            logger.info(f"Order ID: {order.order_id}")
            logger.info(f"  Status: {order.status}")
            logger.info(f"  Order Date: {order.order_placed_date_time}")
            logger.info(f"  Number of items: {len(order.order_items)}")
            
            for idx, item in enumerate(order.order_items, 1):
                fulfilment = item.fulfilment_method or "Unknown"
                is_fbr = fulfilment.upper() == "FBR"
                fbr_status = "✅ FBR" if is_fbr else "❌ Not FBR"
                
                logger.info(f"  Item {idx}:")
                logger.info(f"    orderItemId: {item.order_item_id}")
                logger.info(f"    EAN: {item.ean}")
                logger.info(f"    Quantity: {item.quantity}")
                logger.info(f"    Fulfilment: {fulfilment} {fbr_status}")
                logger.info(f"    Product: {item.product_title or 'N/A'}")
                
                if is_fbr:
                    logger.info(f"    ✅ Can get shipping label for this item")
                else:
                    logger.info(f"    ⚠️  Cannot get shipping label (not FBR)")
                logger.info("")
        
        # Print summary
        logger.info("="*80)
        logger.info("SUMMARY")
        logger.info("="*80)
        total_items = sum(len(o.order_items) for o in all_orders)
        fbr_items = sum(
            sum(1 for item in o.order_items if (item.fulfilment_method or "").upper() == "FBR")
            for o in all_orders
        )
        logger.info(f"Total orders: {len(all_orders)}")
        logger.info(f"Total items: {total_items}")
        logger.info(f"FBR items (can get labels): {fbr_items}")
        logger.info(f"Non-FBR items (cannot get labels): {total_items - fbr_items}")
        
        if fbr_items > 0:
            logger.info("\n✅ You can test shipping labels with these FBR orderItemIds:")
            for order in all_orders:
                for item in order.order_items:
                    if (item.fulfilment_method or "").upper() == "FBR":
                        logger.info(f"  python test_shipping_label.py {item.order_item_id}")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    get_order_item_ids()
