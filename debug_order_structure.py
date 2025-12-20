"""
Debug script to see the actual structure of order items from the API
This helps identify the correct field names
"""

import json
import logging
from bol_api_client import BolAPIClient
from config import BOL_CLIENT_ID, BOL_CLIENT_SECRET, TEST_MODE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_order_structure():
    """Print the actual structure of orders from the API"""
    logger.info("="*80)
    logger.info("DEBUGGING ORDER STRUCTURE FROM API")
    logger.info("="*80)
    
    client = BolAPIClient(BOL_CLIENT_ID, BOL_CLIENT_SECRET, test_mode=TEST_MODE)
    
    try:
        raw_orders = client.get_all_open_orders()
        logger.info(f"\nFound {len(raw_orders)} open orders\n")
        
        if raw_orders:
            # Print first order in detail
            first_order = raw_orders[0]
            logger.info("="*80)
            logger.info("FIRST ORDER STRUCTURE:")
            logger.info("="*80)
            print(json.dumps(first_order, indent=2, default=str))
            
            # Print order items structure
            if 'orderItems' in first_order and first_order['orderItems']:
                logger.info("\n" + "="*80)
                logger.info("FIRST ORDER ITEM STRUCTURE:")
                logger.info("="*80)
                first_item = first_order['orderItems'][0]
                print(json.dumps(first_item, indent=2, default=str))
                
                # Check for fulfilment method
                logger.info("\n" + "="*80)
                logger.info("FULFILMENT METHOD CHECK:")
                logger.info("="*80)
                logger.info(f"fulfilmentMethod (direct): {first_item.get('fulfilmentMethod')}")
                logger.info(f"fulfilment (object): {first_item.get('fulfilment')}")
                if first_item.get('fulfilment'):
                    logger.info(f"fulfilment.method: {first_item.get('fulfilment', {}).get('method')}")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    debug_order_structure()
