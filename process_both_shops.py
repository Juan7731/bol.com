"""
Process orders from BOTH Jean and Trivium shops correctly
This script calls each API separately to ensure correct shop attribution
"""

import logging
from bol_api_client import BolAPIClient
from bol_dtos import Order
from order_processing import (
    classify_orders,
    generate_csv_batches,
    upload_files_sftp,
)
from order_database import init_database, get_unprocessed_orders
from label_uploader import upload_all_labels

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Jean Shop Credentials
JEAN_CLIENT_ID = "051dd4f6-c84e-4b98-876e-77a6727ca48a"
JEAN_CLIENT_SECRET = "O@A58WI8CHfiGhf8JxQT72?oO5BYF)YfhsWTxNZB2BxTlxoxoHKY!IHsFuWb3YLH"

# Trivium Shop Credentials
TRIVIUM_CLIENT_ID = "f418eb2c-ca2c-4138-b5d3-fa89cb800dad"
TRIVIUM_CLIENT_SECRET = "rTj0Z!K1sZThWW!Rgu6u0t2@l62Z8jKXQDcNkx(QH0IX@m+cwiYnHpT4NNi42iVF"


def process_shop(shop_name: str, client_id: str, client_secret: str, test_mode: bool = False, process_all: bool = True):
    """
    Process orders for a specific shop
    
    Args:
        shop_name: "Jean" or "Trivium"
        client_id: Bol.com API client ID
        client_secret: Bol.com API client secret
        test_mode: Whether to use test mode
        process_all: If True, process ALL open orders. If False, only new unprocessed orders
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Processing {shop_name} Shop")
    logger.info(f"{'='*80}")
    
    try:
        # Create API client for this shop
        client = BolAPIClient(client_id, client_secret, test_mode=test_mode)
        
        # Fetch orders
        raw_orders = client.get_all_open_orders()
        all_orders = [Order.from_dict(o) for o in raw_orders]
        
        if not all_orders:
            logger.info(f"No open orders for {shop_name}")
            return {
                'shop': shop_name,
                'total_orders': 0,
                'processed': 0,
                'files_created': [],
                'success': True
            }
        
        logger.info(f"Retrieved {len(all_orders)} open orders for {shop_name}")
        
        # Determine which orders to process
        if process_all:
            # Process ALL open orders
            orders = all_orders
            logger.info(f"Processing ALL {len(orders)} open orders for {shop_name}")
        else:
            # Filter unprocessed orders only
            order_ids = [order.order_id for order in all_orders]
            unprocessed_order_ids = get_unprocessed_orders(order_ids)
            orders = [order for order in all_orders if order.order_id in unprocessed_order_ids]
            
            if not orders:
                logger.info(f"No new unprocessed orders for {shop_name}")
                return {
                    'shop': shop_name,
                    'total_orders': len(all_orders),
                    'processed': 0,
                    'files_created': [],
                    'success': True
                }
            
            logger.info(f"Processing {len(orders)} new orders for {shop_name}")
        
        # Temporarily override DEFAULT_SHOP_NAME
        import order_processing
        original_shop_name = order_processing.DEFAULT_SHOP_NAME
        order_processing.DEFAULT_SHOP_NAME = shop_name
        
        try:
            # Classify and generate CSV files
            grouped = classify_orders(orders)
            logger.info(f"Order breakdown for {shop_name}:")
            logger.info(f"  - Single: {len(grouped.get('Single', []))} orders")
            logger.info(f"  - SingleLine: {len(grouped.get('SingleLine', []))} orders")
            logger.info(f"  - Multi: {len(grouped.get('Multi', []))} orders")
            
            files_created, total_orders = generate_csv_batches(grouped, client)
            
            # Log generated files
            logger.info(f"Generated {len(files_created)} CSV files for {shop_name}:")
            for f in files_created:
                import os
                logger.info(f"  - {os.path.basename(f)}")
            
            # Upload CSV files
            if files_created:
                logger.info(f"Uploading {len(files_created)} CSV files for {shop_name}...")
                upload_files_sftp(files_created)
                logger.info(f"✅ CSV files uploaded to SFTP /Batches/ for {shop_name}")
                
                # Upload label PDFs
                try:
                    logger.info(f"Uploading label PDFs for {shop_name}...")
                    upload_all_labels()
                    logger.info(f"✅ Label PDFs uploaded to SFTP /label/ for {shop_name}")
                except Exception as label_error:
                    logger.error(f"❌ Failed to upload label PDFs for {shop_name}: {label_error}")
                    logger.info(f"   Labels are saved locally in 'label/' folder")
            
            return {
                'shop': shop_name,
                'total_orders': len(all_orders),
                'processed': total_orders,
                'files_created': files_created,
                'success': True
            }
            
        finally:
            # Restore original shop name
            order_processing.DEFAULT_SHOP_NAME = original_shop_name
        
    except Exception as e:
        logger.error(f"❌ Error processing {shop_name}: {e}")
        import traceback
        traceback.print_exc()
        return {
            'shop': shop_name,
            'total_orders': 0,
            'processed': 0,
            'files_created': [],
            'success': False,
            'error': str(e)
        }


def main():
    """Process both Jean and Trivium shops"""
    print("\n" + "="*80)
    print("PROCESSING BOTH SHOPS: JEAN & TRIVIUM")
    print("Processing ALL OPEN ORDERS")
    print("="*80)
    
    # Initialize database
    init_database()
    
    # Process Jean shop - ALL OPEN ORDERS
    jean_result = process_shop("Jean", JEAN_CLIENT_ID, JEAN_CLIENT_SECRET, test_mode=False, process_all=True)
    
    # Process Trivium shop - ALL OPEN ORDERS
    trivium_result = process_shop("Trivium", TRIVIUM_CLIENT_ID, TRIVIUM_CLIENT_SECRET, test_mode=False, process_all=True)
    
    # Summary
    print("\n" + "="*80)
    print("PROCESSING SUMMARY")
    print("="*80)
    
    print(f"\n📊 Jean Shop:")
    print(f"   Total orders: {jean_result['total_orders']}")
    print(f"   Processed: {jean_result['processed']}")
    print(f"   Files created: {len(jean_result['files_created'])}")
    if jean_result['files_created']:
        for f in jean_result['files_created']:
            print(f"      - {f}")
    print(f"   Status: {'✅ Success' if jean_result['success'] else '❌ Failed'}")
    
    print(f"\n📊 Trivium Shop:")
    print(f"   Total orders: {trivium_result['total_orders']}")
    print(f"   Processed: {trivium_result['processed']}")
    print(f"   Files created: {len(trivium_result['files_created'])}")
    if trivium_result['files_created']:
        for f in trivium_result['files_created']:
            print(f"      - {f}")
    print(f"   Status: {'✅ Success' if trivium_result['success'] else '❌ Failed'}")
    
    total_processed = jean_result['processed'] + trivium_result['processed']
    print(f"\n🎯 Total orders processed: {total_processed}")
    print("="*80)
    
    return jean_result['success'] and trivium_result['success']


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)

