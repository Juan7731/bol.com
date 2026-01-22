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
    # upload_labels_for_csv_files: envia apenas os PDFs referentes aos pedidos presentes nos CSVs gerados
    from label_uploader import upload_labels_for_csv_files
    LABEL_UPLOADER_AVAILABLE = True
except ImportError:
    LABEL_UPLOADER_AVAILABLE = False
from order_database import init_database, get_unprocessed_orders
from config_manager import get_active_bol_accounts, get_config_summary

logger = logging.getLogger(__name__)


def process_account(account_name: str, client_id: str, client_secret: str, 
                    shop_name: str, test_mode: bool = False) -> Dict:
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
        
        # Fetch orders - get list first, then fetch individual orders for complete details
        try:
            logger.info(f"📋 Fetching list of open orders for {account_name}...")
            raw_orders_list = client.get_all_open_orders()
            
            if not raw_orders_list:
                logger.info(f"No open orders for account {account_name}")
                all_orders = []
            else:
                logger.info(f"📋 Found {len(raw_orders_list)} open order(s) for {account_name}, fetching individual order details...")
                
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
        
        # Debug: Log order details before classification
        logger.info(f"📋 Debug: Checking order details for {account_name}...")
        for order in orders:
            logger.info(f"   Order {order.order_id}:")
            logger.info(f"      - Status: {order.status}")
            logger.info(f"      - Order items count: {len(order.order_items)}")
            if order.order_items:
                for idx, item in enumerate(order.order_items):
                    logger.info(f"      - Item {idx + 1}: orderItemId={item.order_item_id}, EAN={item.ean}, quantity={item.quantity}")
            else:
                logger.warning(f"      ⚠️ Order {order.order_id} has NO order items!")
        
        # Classify orders
        try:
            grouped = classify_orders(orders)
            
            # Log classification results
            total_classified = sum(len(grouped[cat]) for cat in grouped)
            logger.info(f"📋 Classification results for {account_name}:")
            logger.info(f"   Single: {len(grouped['Single'])} order(s)")
            logger.info(f"   SingleLine: {len(grouped['SingleLine'])} order(s)")
            logger.info(f"   Multi: {len(grouped['Multi'])} order(s)")
            logger.info(f"   Total classified: {total_classified} out of {len(orders)} order(s)")
            
            if total_classified == 0:
                logger.error(f"❌ No orders were classified for {account_name}!")
                logger.error(f"   This means orders cannot be processed.")
                logger.error(f"   Check the order details above to see why.")
        except Exception as classify_error:
            logger.error(f"Failed to classify orders for {account_name}: {classify_error}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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
            # Verify files exist before attempting upload
            import os
            existing_files = []
            for file_path in files_created:
                if os.path.exists(file_path):
                    existing_files.append(file_path)
                    logger.debug(f"✅ Arquivo encontrado: {file_path}")
                else:
                    logger.warning(f"⚠️  Arquivo não encontrado (será pulado): {file_path}")
            
            if existing_files:
                logger.info(f"📤 Preparando upload de {len(existing_files)} arquivo(s) CSV para {account_name}...")
                try:
                    upload_files_sftp(existing_files)
                    logger.info(f"✅ Upload de arquivos CSV concluído para {account_name}")
                except Exception as upload_error:
                    logger.error(f"❌ Falha no upload de arquivos CSV para {account_name}: {upload_error}")
                    import traceback
                    logger.error(f"   Traceback completo: {traceback.format_exc()}")
                    # Continue anyway - files are created locally
            else:
                logger.warning(f"⚠️  Nenhum arquivo CSV válido encontrado para upload para {account_name}")
        else:
            logger.info(f"ℹ️  Nenhum arquivo CSV gerado para {account_name} (nenhum pedido para processar)")
        
        # Upload label PDFs (apenas dos pedidos processados neste batch)
        if LABEL_UPLOADER_AVAILABLE and files_created:
            try:
                logger.info(f"📤 Preparando upload de labels PDF para {account_name} (apenas dos pedidos processados)...")
                upload_labels_for_csv_files(files_created)
                logger.info(f"✅ Upload de labels PDF concluído para {account_name}")
            except Exception as label_error:
                logger.error(f"❌ Falha no upload de labels PDF para {account_name}: {label_error}")
                import traceback
                logger.error(f"   Traceback completo: {traceback.format_exc()}")
                # Continue anyway - labels are saved locally
        elif not files_created:
            logger.info(f"ℹ️  Nenhum arquivo CSV gerado - pulando upload de labels PDF para {account_name}")
        else:
            logger.warning(f"⚠️  Label uploader não disponível - PDFs permanecem na pasta local 'label/'")
        
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
    
    for account_index, account in enumerate(active_accounts, 1):
        account_name = account['name']
        client_id = account['client_id']
        client_secret = account['client_secret']
        
        # Use account name as shop name, or default
        shop_name = account_name if account_name in ['Trivium', 'Jean'] else default_shop
        
        # PRODUCTION MODE: Always use test_mode=False for live labels
        # Do not read from config - force production mode
        test_mode = False
        
        # Log mode for clarity
        logger.info("")
        logger.info("="*80)
        logger.info(f"Processing Account {account_index}/{len(active_accounts)}: {account_name} (Shop: {shop_name})")
        logger.info("="*80)
        logger.info(f"✅ Modo PRODUÇÃO para {account_name} - Labels de PRODUÇÃO (LIVE) serão criados")
        
        try:
            result = process_account(
                account_name=account_name,
                client_id=client_id,
                client_secret=client_secret,
                shop_name=shop_name,
                test_mode=False  # PRODUCTION MODE - LIVE LABELS
            )
            
            results.append(result)
            total_orders_all += result.get('processed', 0)
            
            # Log result
            if result.get('success', False):
                logger.info(f"✅ Successfully processed {account_name}: {result.get('processed', 0)} order(s)")
            else:
                logger.error(f"❌ Failed to process {account_name}: {result.get('error', 'Unknown error')}")
        except Exception as account_error:
            logger.error(f"❌ Exception processing account {account_name}: {account_error}")
            import traceback
            logger.error(traceback.format_exc())
            # Add error result but continue with next account
            results.append({
                'account': account_name,
                'shop': shop_name,
                'total_orders': 0,
                'processed': 0,
                'files_created': [],
                'success': False,
                'error': str(account_error)
            })
    
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

