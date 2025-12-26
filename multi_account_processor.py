"""
Multi-Account Order Processor

Processes orders from multiple Bol.com accounts (Trivium, Jean, etc.)
"""

import logging
from typing import List, Dict, Optional

from bol_api_client import BolAPIClient
from bol_dtos import Order
import order_processing
from order_processing import (
    classify_orders,
    generate_excel_batches,
    upload_files_sftp,
    send_summary_email,
    run_processing_once,
)

# Import label uploader for automatic PDF upload
try:
    from label_uploader import upload_all_labels
    LABEL_UPLOADER_AVAILABLE = True
except ImportError:
    LABEL_UPLOADER_AVAILABLE = False
from order_database import init_database, get_unprocessed_orders
from config_manager import get_active_bol_accounts, get_config_summary

logger = logging.getLogger(__name__)


def process_account(account_name: str, client_id: str, client_secret: str, 
                    shop_name: str, test_mode: bool = True) -> Dict:
    """
    Process orders for a single Bol.com account.
    
    Args:
        account_name: Account name (e.g., "Trivium", "Jean")
        client_id: Bol.com client ID
        client_secret: Bol.com client secret
        shop_name: Shop name to use in Excel files
        test_mode: Whether to use test mode
        
    Returns:
        Dictionary with processing results
    """
    logger.info(f"Processing account: {account_name} (Shop: {shop_name})")
    
    try:
        # Initialize database (shared across all accounts)
        try:
            init_database()
        except Exception as db_error:
            logger.warning(f"Database initialization warning for {account_name}: {db_error} (continuing anyway)")
        
        # Create API client for this account
        try:
            client = BolAPIClient(client_id, client_secret, test_mode=test_mode)
        except Exception as client_error:
            logger.error(f"Failed to create API client for {account_name}: {client_error}")
            raise
        
        # Fetch orders
        try:
            raw_orders = client.get_all_open_orders()
            all_orders = [Order.from_dict(o) for o in raw_orders]
        except Exception as fetch_error:
            logger.error(f"Failed to fetch orders for {account_name}: {fetch_error}")
            raise
        
        if not all_orders:
            logger.info(f"No open orders for account {account_name}")
            return {
                'account': account_name,
                'shop': shop_name,
                'total_orders': 0,
                'processed': 0,
                'files_created': [],
                'success': True
            }
        
        # Filter out already processed orders
        try:
            order_ids = [order.order_id for order in all_orders]
            unprocessed_order_ids = get_unprocessed_orders(order_ids)
            orders = [order for order in all_orders if order.order_id in unprocessed_order_ids]
        except Exception as filter_error:
            logger.error(f"Failed to filter orders for {account_name}: {filter_error}")
            raise
        
        if not orders:
            logger.info(f"No new unprocessed orders for account {account_name} (total open: {len(all_orders)})")
            return {
                'account': account_name,
                'shop': shop_name,
                'total_orders': len(all_orders),
                'processed': 0,
                'files_created': [],
                'success': True
            }
        
        logger.info(f"Processing {len(orders)} new orders for {account_name} (from {len(all_orders)} total)")
        
        # Classify orders
        try:
            grouped = classify_orders(orders)
        except Exception as classify_error:
            logger.error(f"Failed to classify orders for {account_name}: {classify_error}")
            raise
        
        # Temporarily override DEFAULT_SHOP_NAME to use the correct shop for this account
        original_shop_name = order_processing.DEFAULT_SHOP_NAME
        order_processing.DEFAULT_SHOP_NAME = shop_name
        
        try:
            # Generate Excel files with the correct shop name
            files_created, total_orders = generate_excel_batches(grouped, client)
        finally:
            # Restore original shop name (always restore, even if error)
            order_processing.DEFAULT_SHOP_NAME = original_shop_name
        
        # Upload CSV files
        if files_created:
            try:
                upload_files_sftp(files_created)
            except Exception as upload_error:
                logger.error(f"Failed to upload CSV files for {account_name}: {upload_error}")
                # Continue anyway - files are created locally
            
            # Upload label PDFs
            if LABEL_UPLOADER_AVAILABLE:
                try:
                    upload_all_labels()
                except Exception as label_error:
                    logger.error(f"Failed to upload label PDFs for {account_name}: {label_error}")
                    # Continue anyway - labels are saved locally
        
        # Send email summary (non-critical, don't fail if this errors)
        try:
            send_summary_email(total_orders, files_created)
        except Exception as email_error:
            logger.warning(f"Failed to send email for {account_name}: {email_error} (non-critical)")
        
        logger.info(f"✅ Successfully completed processing for {account_name}: {total_orders} order(s) processed")
        
        return {
            'account': account_name,
            'shop': shop_name,
            'total_orders': len(all_orders),
            'processed': total_orders,
            'files_created': files_created,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing account {account_name}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'account': account_name,
            'shop': shop_name,
            'total_orders': 0,
            'processed': 0,
            'files_created': [],
            'success': False,
            'error': str(e)
        }


def process_all_accounts() -> Dict:
    """
    Process orders from all active Bol.com accounts.
    
    Returns:
        Dictionary with processing results for each account
    """
    logger.info("="*80)
    logger.info("MULTI-ACCOUNT ORDER PROCESSING")
    logger.info("="*80)
    
    # Get active accounts
    active_accounts = get_active_bol_accounts()
    config = get_config_summary()
    default_shop = config.get('default_shop', 'Trivium')
    
    if not active_accounts:
        logger.warning("No active Bol.com accounts found")
        return {
            'accounts_processed': 0,
            'total_orders': 0,
            'results': []
        }
    
    results = []
    total_orders_all = 0
    
    for account in active_accounts:
        account_name = account['name']
        client_id = account['client_id']
        client_secret = account['client_secret']
        
        # Use account name as shop name, or default
        shop_name = account_name if account_name in ['Trivium', 'Jean'] else default_shop
        
        # Get test_mode from config, default to False (production)
        test_mode = config.get('test_mode', False)
        
        result = process_account(
            account_name=account_name,
            client_id=client_id,
            client_secret=client_secret,
            shop_name=shop_name,
            test_mode=test_mode
        )
        
        results.append(result)
        total_orders_all += result.get('processed', 0)
    
    logger.info("="*80)
    logger.info(f"Multi-account processing complete:")
    logger.info(f"  Accounts processed: {len(results)}")
    logger.info(f"  Total orders processed: {total_orders_all}")
    logger.info("="*80)
    
    return {
        'accounts_processed': len(results),
        'total_orders': total_orders_all,
        'results': results
    }


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Process all active accounts
    process_all_accounts()

