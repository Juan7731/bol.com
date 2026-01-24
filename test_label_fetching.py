"""
Test script to verify shipping label fetching works for a specific order item
"""

import logging
import sys
from bol_api_client import BolAPIClient
from bol_dtos import Order
from order_processing import _fetch_zpl_label
from config_manager import get_active_bol_accounts

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_label_fetching(order_item_id: str = None, account_name: str = None):
    """Test shipping label fetching for a specific order item"""
    logger.info("="*80)
    logger.info("🧪 TESTING SHIPPING LABEL FETCHING")
    logger.info("="*80)
    logger.info("")
    
    # Get account
    active_accounts = get_active_bol_accounts()
    if not active_accounts:
        logger.error("❌ No active accounts found")
        return False
    
    # Find account
    account = None
    if account_name:
        for acc in active_accounts:
            if acc['name'].lower() == account_name.lower():
                account = acc
                break
    else:
        account = active_accounts[0]
    
    if not account:
        logger.error(f"❌ Account '{account_name}' not found")
        return False
    
    logger.info(f"📋 Using account: {account['name']}")
    
    # Create client
    client = BolAPIClient(account['client_id'], account['client_secret'], test_mode=False)
    
    # If order_item_id provided, test with that
    if order_item_id:
        logger.info(f"🧪 Testing with order item ID: {order_item_id}")
        logger.info("")
        
        try:
            label_id = _fetch_zpl_label(client, order_item_id, "TEST_ORDER", quantity=1)
            
            if label_id:
                logger.info("")
                logger.info("="*80)
                logger.info("✅ SUCCESS: Shipping label fetched!")
                logger.info("="*80)
                logger.info(f"   Label ID: {label_id}")
                
                import os
                pdf_path = os.path.join("label", f"{label_id}.pdf")
                if os.path.exists(pdf_path):
                    size = os.path.getsize(pdf_path)
                    logger.info(f"   PDF file: {pdf_path} ({size} bytes)")
                    logger.info("✅ PDF file verified")
                    return True
                else:
                    logger.warning(f"⚠️ PDF file not found: {pdf_path}")
                    return False
            else:
                logger.error("")
                logger.error("="*80)
                logger.error("❌ FAILED: No label ID returned")
                logger.error("="*80)
                logger.error("   Check the logs above for errors")
                return False
                
        except Exception as e:
            logger.error("")
            logger.error("="*80)
            logger.error("❌ EXCEPTION: Label fetching failed")
            logger.error("="*80)
            logger.error(f"   Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    # Otherwise, find an FBR order item to test
    logger.info("📋 Finding FBR order items to test...")
    raw_orders_list = client.get_all_open_orders()
    
    if not raw_orders_list:
        logger.warning("⚠️ No open orders found")
        return False
    
    # Get first order with FBR items
    for order_summary in raw_orders_list:
        order_id = order_summary.get('orderId')
        if not order_id:
            continue
        
        try:
            full_order_data = client.get_order(order_id)
            order = Order.from_dict(full_order_data)
            
            # Find FBR item
            for item in order.order_items:
                if (item.fulfilment_method or "").upper() == "FBR":
                    logger.info(f"✅ Found FBR item: {item.order_item_id} in order {order_id}")
                    logger.info("")
                    
                    # Test label fetching
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
                        logger.info("✅ SUCCESS: Shipping label fetched!")
                        logger.info("="*80)
                        logger.info(f"   Order ID: {order.order_id}")
                        logger.info(f"   Order Item ID: {item.order_item_id}")
                        logger.info(f"   Label ID: {label_id}")
                        
                        import os
                        pdf_path = os.path.join("label", f"{label_id}.pdf")
                        if os.path.exists(pdf_path):
                            size = os.path.getsize(pdf_path)
                            logger.info(f"   PDF file: {pdf_path} ({size} bytes)")
                            logger.info("✅ PDF file verified")
                            return True
                    else:
                        logger.error("❌ Failed to fetch label")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Error processing order {order_id}: {e}")
            continue
    
    logger.warning("⚠️ No FBR items found to test")
    return False


if __name__ == "__main__":
    import sys
    order_item_id = sys.argv[1] if len(sys.argv) > 1 else None
    account_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = test_label_fetching(order_item_id, account_name)
    sys.exit(0 if success else 1)
