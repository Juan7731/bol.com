"""
Script to check the actual structure of order items from the API
This will help us see where the fulfilment method is stored
"""

import logging
import json
from bol_api_client import BolAPIClient
from config import BOL_CLIENT_ID, BOL_CLIENT_SECRET, TEST_MODE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_fulfilment_structure():
    """Check the actual API response structure for order items"""
    logger.info("="*80)
    logger.info("CHECKING ORDER ITEM STRUCTURE FROM API")
    logger.info("="*80)
    
    client = BolAPIClient(BOL_CLIENT_ID, BOL_CLIENT_SECRET, test_mode=TEST_MODE)
    
    try:
        raw_orders = client.get_all_open_orders()
        
        if not raw_orders:
            logger.warning("No open orders found")
            return
        
        # Get first order
        first_order = raw_orders[0]
        logger.info(f"\nOrder ID: {first_order.get('orderId', 'N/A')}")
        logger.info(f"Order keys: {list(first_order.keys())}\n")
        
        # Check order items
        order_items = first_order.get('orderItems', [])
        if not order_items:
            logger.warning("No order items found")
            return
        
        logger.info(f"Found {len(order_items)} order item(s)\n")
        
        # Print first order item structure
        first_item = order_items[0]
        logger.info("="*80)
        logger.info("FIRST ORDER ITEM STRUCTURE:")
        logger.info("="*80)
        logger.info(json.dumps(first_item, indent=2, default=str))
        
        # Check for fulfilment-related keys
        logger.info("\n" + "="*80)
        logger.info("CHECKING FOR FULFILMENT-RELATED KEYS:")
        logger.info("="*80)
        
        def find_keys(obj, prefix=""):
            """Recursively find all keys"""
            keys = []
            if isinstance(obj, dict):
                for key, value in obj.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    keys.append(full_key)
                    if isinstance(value, dict):
                        keys.extend(find_keys(value, full_key))
            return keys
        
        all_keys = find_keys(first_item)
        fulfilment_keys = [k for k in all_keys if 'fulfil' in k.lower() or 'fbr' in k.lower()]
        
        if fulfilment_keys:
            logger.info("Found fulfilment-related keys:")
            for key in fulfilment_keys:
                logger.info(f"  - {key}")
        else:
            logger.warning("No fulfilment-related keys found!")
        
        # Check common locations
        logger.info("\n" + "="*80)
        logger.info("CHECKING COMMON LOCATIONS:")
        logger.info("="*80)
        
        locations = [
            ('fulfilment', first_item.get('fulfilment')),
            ('fulfilmentMethod', first_item.get('fulfilmentMethod')),
            ('fulfilment.method', first_item.get('fulfilment', {}).get('method')),
            ('fulfilment.type', first_item.get('fulfilment', {}).get('type')),
            ('fulfilment.fulfilmentMethod', first_item.get('fulfilment', {}).get('fulfilmentMethod')),
        ]
        
        for location, value in locations:
            if value is not None:
                logger.info(f"✅ {location}: {value}")
            else:
                logger.info(f"❌ {location}: Not found")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    check_fulfilment_structure()
