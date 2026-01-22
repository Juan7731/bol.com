"""
Debug script to check why orders are not being classified
"""

import logging
import json
from bol_api_client import BolAPIClient
from bol_dtos import Order
from config_manager import get_active_bol_accounts

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def debug_order_classification():
    """Debug order classification issues"""
    logger.info("="*80)
    logger.info("🔍 DEBUGGING ORDER CLASSIFICATION")
    logger.info("="*80)
    logger.info("")
    
    # Get active accounts
    active_accounts = get_active_bol_accounts()
    if not active_accounts:
        logger.error("❌ No active accounts found")
        return
    
    # Use first active account
    account = active_accounts[0]
    logger.info(f"📋 Using account: {account['name']}")
    logger.info("")
    
    # Create API client
    client = BolAPIClient(account['client_id'], account['client_secret'], test_mode=False)
    
    # Fetch orders
    logger.info("📋 Fetching open orders...")
    raw_orders_list = client.get_all_open_orders()
    logger.info(f"✅ Found {len(raw_orders_list)} open order(s)")
    logger.info("")
    
    if not raw_orders_list:
        logger.warning("⚠️ No open orders found")
        return
    
    # Fetch individual orders
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
            
            logger.info("")
            logger.info("="*80)
            logger.info(f"ORDER: {order_id}")
            logger.info("="*80)
            logger.info(f"Status: {order.status}")
            logger.info(f"Order items count: {len(order.order_items)}")
            logger.info(f"Order placed: {order.order_placed_date_time}")
            logger.info("")
            
            if not order.order_items:
                logger.error("❌ Order has NO order items!")
                logger.info("Raw API response structure:")
                logger.info(json.dumps(full_order_data, indent=2, default=str)[:2000])
            else:
                logger.info("Order Items:")
                for idx, item in enumerate(order.order_items):
                    logger.info(f"  Item {idx + 1}:")
                    logger.info(f"    - orderItemId: {item.order_item_id}")
                    logger.info(f"    - EAN: {item.ean}")
                    logger.info(f"    - Quantity: {item.quantity}")
                    logger.info(f"    - Fulfilment: {item.fulfilment_method}")
                    logger.info(f"    - Product: {item.product_title}")
                
                # Check classification
                logger.info("")
                logger.info("Classification:")
                logger.info(f"  - is_single: {order.is_single}")
                logger.info(f"  - is_singleline: {order.is_singleline}")
                logger.info(f"  - is_multi: {order.is_multi}")
                logger.info(f"  - category: {order.category}")
                logger.info(f"  - unique_eans: {order.unique_eans}")
                logger.info(f"  - total_items: {order.total_items}")
                
                if order.category == "Unknown":
                    logger.error("❌ Order category is 'Unknown' - cannot be processed!")
                    logger.error("   Reasons could be:")
                    logger.error("   - No EANs in order items")
                    logger.error("   - Order items structure doesn't match expected format")
                    logger.error("   - Order has 0 items")
                else:
                    logger.info(f"✅ Order can be classified as: {order.category}")
        
        except Exception as e:
            logger.error(f"❌ Failed to process order {order_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            continue
    
    logger.info("")
    logger.info("="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Total orders fetched: {len(all_orders)}")
    
    # Classify orders
    from order_processing import classify_orders
    grouped = classify_orders(all_orders)
    
    logger.info(f"Single: {len(grouped['Single'])}")
    logger.info(f"SingleLine: {len(grouped['SingleLine'])}")
    logger.info(f"Multi: {len(grouped['Multi'])}")
    
    total_classified = sum(len(grouped[cat]) for cat in grouped)
    if total_classified == 0:
        logger.error("")
        logger.error("❌ NO ORDERS WERE CLASSIFIED!")
        logger.error("   This is why no CSV files are being generated.")
        logger.error("   Check the order details above to see why.")


if __name__ == "__main__":
    debug_order_classification()
