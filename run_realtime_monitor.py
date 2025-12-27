"""
Real-Time Order Monitor - Multi-Account Processing

This script monitors for new orders every minute and processes them automatically.
- Checks both Jean and Trivium accounts
- Runs every minute continuously
- Processes orders automatically when found
- Also processes at scheduled times from system_config.json
- Production mode (test_mode=False)
"""

import logging
import sys
import time
import os
from datetime import datetime, date
from typing import Dict, List
import signal
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
running = True
STOP_FLAG_FILE = "monitor_stop_flag.txt"


def check_stop_flag() -> bool:
    """Check if stop flag file exists"""
    try:
        if os.path.exists(STOP_FLAG_FILE):
            with open(STOP_FLAG_FILE, 'r') as f:
                content = f.read().strip()
                return content == "1" or content.lower() == "stop"
    except Exception:
        pass
    return False


def clear_stop_flag():
    """Clear the stop flag file"""
    try:
        if os.path.exists(STOP_FLAG_FILE):
            with open(STOP_FLAG_FILE, 'w') as f:
                f.write("0")
    except Exception:
        pass


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global running
    logger.info("")
    logger.info("⚠️  Shutdown signal received. Stopping monitor...")
    running = False
    # Save any partial data
    save_partial_data()


def load_processing_times() -> List[str]:
    """Load processing times from system_config.json"""
    try:
        with open('system_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            times = config.get('processing_times', [])
            # Filter out empty strings and normalize
            valid_times = []
            for t in times:
                if t and t.strip():
                    try:
                        # Validate time format (HH:MM)
                        datetime.strptime(t.strip(), '%H:%M')
                        valid_times.append(t.strip())
                    except ValueError:
                        logger.warning(f"Invalid time format: {t}")
            return valid_times
    except Exception as e:
        logger.error(f"Failed to load processing times: {e}")
        return []


def normalize_time_string(t: str) -> str:
    """Normalize time string to HH:MM format"""
    try:
        dt = datetime.strptime(t.strip(), "%H:%M")
        return dt.strftime("%H:%M")
    except ValueError:
        return ""


def save_partial_data():
    """Save any partial processing data before stopping"""
    try:
        logger.info("💾 Ensuring all processing data is saved...")
        
        # CSVs and PDFs are already saved immediately during processing:
        # - CSVs are saved in _create_csv_for_category() when written
        # - PDFs are saved in _save_pdf_label() when downloaded
        # - Orders are marked as processed in the database immediately
        
        # Verify that batches and label folders exist and have data
        import os
        from datetime import datetime
        
        batches_dir = os.path.join("batches", datetime.now().strftime("%Y%m%d"))
        label_dir = "label"
        
        csv_count = 0
        pdf_count = 0
        
        if os.path.exists(batches_dir):
            csv_files = [f for f in os.listdir(batches_dir) if f.endswith('.csv')]
            csv_count = len(csv_files)
        
        if os.path.exists(label_dir):
            pdf_files = [f for f in os.listdir(label_dir) if f.endswith('.pdf')]
            pdf_count = len(pdf_files)
        
        logger.info(f"✅ Data saved: {csv_count} CSV file(s) in batches/, {pdf_count} PDF file(s) in label/")
        logger.info("✅ All processed data is safely saved in batches/ and label/ folders")
        
    except Exception as e:
        logger.error(f"Error verifying saved data: {e}")


def process_orders_realtime() -> Dict:
    """
    Process orders from all active accounts in real-time.
    Returns processing results.
    Checks for stop flag during processing.
    """
    try:
        from multi_account_processor import process_account
        from config_manager import get_active_bol_accounts, get_config_summary
        
        # Check stop flag before starting
        if check_stop_flag():
            logger.warning("⚠️  Stop flag detected. Saving partial data and stopping...")
            save_partial_data()
            return {
                'accounts_processed': 0,
                'total_orders': 0,
                'results': [],
                'stopped': True
            }
        
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
        
        logger.info(f"Found {len(active_accounts)} active account(s) to process")
        
        results = []
        total_orders_all = 0
        account_index = 0
        
        for account in active_accounts:
            # Check stop flag before processing each account
            if check_stop_flag():
                logger.warning("⚠️  Stop flag detected during account processing. Saving partial data...")
                save_partial_data()
                break
            
            account_index += 1
            account_name = account.get('name', 'Unknown')
            client_id = account.get('client_id', '')
            client_secret = account.get('client_secret', '')
            
            if not client_id or not client_secret:
                logger.error(f"⚠️  Skipping account {account_name}: Missing credentials")
                results.append({
                    'account': account_name,
                    'shop': account_name,
                    'total_orders': 0,
                    'processed': 0,
                    'success': False,
                    'error': 'Missing credentials'
                })
                continue
            
            # Use account name as shop name
            shop_name = account_name if account_name in ['Trivium', 'Jean'] else default_shop
            
            logger.info("")
            logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.info(f"Processing Account {account_index}/{len(active_accounts)}: {account_name} (Shop: {shop_name})")
            logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            try:
                # Check stop flag before processing this account
                if check_stop_flag():
                    logger.warning(f"⚠️  Stop flag detected before processing {account_name}. Saving data...")
                    save_partial_data()
                    break
                
                # Process account in PRODUCTION mode
                result = process_account(
                    account_name=account_name,
                    client_id=client_id,
                    client_secret=client_secret,
                    shop_name=shop_name,
                    test_mode=False  # PRODUCTION MODE
                )
                
                results.append(result)
                
                # Only count orders that were actually processed
                orders_processed = result.get('processed', 0)
                total_orders_all += orders_processed
                
                if result.get('success', False):
                    if orders_processed > 0:
                        logger.info(f"✅ Account {account_name}: Successfully processed {orders_processed} order(s)")
                    else:
                        logger.info(f"✅ Account {account_name}: No new orders (check completed successfully)")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    logger.error(f"❌ Account {account_name}: Processing failed - {error_msg}")
                
                # Check stop flag after processing each account
                if check_stop_flag():
                    logger.warning("⚠️  Stop flag detected after account processing. Saving data and stopping...")
                    save_partial_data()
                    break
                    
            except Exception as account_error:
                logger.error(f"❌ Exception while processing account {account_name}: {account_error}")
                import traceback
                logger.error(traceback.format_exc())
                results.append({
                    'account': account_name,
                    'shop': shop_name,
                    'total_orders': 0,
                    'processed': 0,
                    'success': False,
                    'error': str(account_error)
                })
                # Continue processing next account even if this one failed
                continue
        
        # Summary
        logger.info("")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info(f"Processing Summary: {len(results)} account(s) processed, {total_orders_all} total order(s)")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return {
            'accounts_processed': len(results),
            'total_orders': total_orders_all,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"❌ Fatal error processing orders: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'accounts_processed': 0,
            'total_orders': 0,
            'results': [],
            'error': str(e)
        }


def main():
    """Main real-time monitoring loop"""
    global running
    
    # Clear stop flag on startup
    clear_stop_flag()
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load scheduled processing times
    scheduled_times = load_processing_times()
    scheduled_times = [normalize_time_string(t) for t in scheduled_times]
    scheduled_times = [t for t in scheduled_times if t]
    
    logger.info("="*80)
    logger.info("REAL-TIME ORDER MONITOR - Multi-Account Processing")
    logger.info("="*80)
    logger.info("⚠️  Running in PRODUCTION mode")
    logger.info("⏰  Checking for new orders every 60 seconds")
    
    if scheduled_times:
        logger.info("📅 Scheduled processing times (auto-run):")
        for i, t in enumerate(scheduled_times, 1):
            logger.info(f"   {i}. {t}")
        logger.info("   (Will process automatically at these times even if no new orders)")
    else:
        logger.info("📅 No scheduled times configured (checking every minute only)")
    
    logger.info("⌨️  Press Ctrl+C to stop or use Admin Panel Stop button")
    logger.info("="*80)
    logger.info("")
    
    check_count = 0
    total_orders_processed = 0
    last_scheduled_run: Dict[str, date] = {}  # time_str -> date when last run at scheduled time
    
    try:
        while running:
            # Check stop flag at the start of each loop iteration
            if check_stop_flag():
                logger.warning("")
                logger.warning("⚠️  Stop flag detected from Admin Panel. Stopping monitor...")
                save_partial_data()
                break
            check_count += 1
            now = datetime.now()
            current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            current_time_hm = now.strftime("%H:%M")
            today = now.date()
            
            # Check if this is a scheduled time
            is_scheduled_time = current_time_hm in scheduled_times
            should_force_process = False
            
            if is_scheduled_time:
                # Check if we already processed at this scheduled time today
                if last_scheduled_run.get(current_time_hm) != today:
                    should_force_process = True
                    last_scheduled_run[current_time_hm] = today
            
            logger.info("")
            logger.info("─" * 80)
            if should_force_process:
                logger.info(f"CHECK #{check_count} - {current_time_str} - ⏰ SCHEDULED TIME: {current_time_hm}")
            else:
                logger.info(f"CHECK #{check_count} - {current_time_str}")
            logger.info("─" * 80)
            
            # Process orders
            result = process_orders_realtime()
            
            orders_this_check = result.get('total_orders', 0)
            accounts_processed = result.get('accounts_processed', 0)
            total_orders_processed += orders_this_check
            
            # Show detailed results for each account
            results_list = result.get('results', [])
            if results_list:
                logger.info("")
                logger.info("Account Processing Results:")
                for acc_result in results_list:
                    acc_name = acc_result.get('account', 'Unknown')
                    acc_processed = acc_result.get('processed', 0)
                    acc_total = acc_result.get('total_orders', 0)
                    acc_success = acc_result.get('success', False)
                    
                    if acc_success:
                        if acc_processed > 0:
                            logger.info(f"  ✅ {acc_name}: {acc_processed} order(s) processed (from {acc_total} total)")
                        else:
                            logger.info(f"  ✅ {acc_name}: No new orders (checked {acc_total} total)")
                    else:
                        error_msg = acc_result.get('error', 'Unknown error')
                        logger.error(f"  ❌ {acc_name}: Failed - {error_msg}")
            
            # Summary for this check
            if should_force_process:
                if orders_this_check > 0:
                    logger.info("")
                    logger.info(f"✅ Scheduled check #{check_count} complete: {orders_this_check} order(s) processed from {accounts_processed} account(s)")
                else:
                    logger.info("")
                    logger.info(f"✅ Scheduled check #{check_count} complete: No new orders from {accounts_processed} account(s) (scheduled run completed)")
            else:
                if orders_this_check > 0:
                    logger.info("")
                    logger.info(f"✅ Check #{check_count} complete: {orders_this_check} order(s) processed from {accounts_processed} account(s)")
                else:
                    logger.info("")
                    logger.info(f"ℹ️  Check #{check_count} complete: No new orders from {accounts_processed} account(s)")
            
            logger.info(f"📊 Total orders processed since start: {total_orders_processed}")
            
            # Show next scheduled time
            if scheduled_times:
                next_scheduled = None
                for t in sorted(scheduled_times):
                    if t > current_time_hm:
                        next_scheduled = t
                        break
                if not next_scheduled and scheduled_times:
                    # Next scheduled time is tomorrow
                    next_scheduled = scheduled_times[0]
                
                if next_scheduled:
                    logger.info(f"📅 Next scheduled processing: {next_scheduled}")
            
            # Wait 60 seconds before next check
            if running and not check_stop_flag():
                logger.info("")
                logger.info(f"⏳ Next check in 60 seconds... (Ctrl+C or Admin Panel to stop)")
                
                # Sleep in 1-second intervals to check for shutdown signal and stop flag
                for i in range(60):
                    if not running or check_stop_flag():
                        if check_stop_flag():
                            logger.warning("⚠️  Stop flag detected during wait. Stopping...")
                            save_partial_data()
                        break
                    time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("")
        logger.info("⚠️  Monitor stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error in monitor: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        # Clear stop flag
        clear_stop_flag()
        
        # Save any remaining partial data
        save_partial_data()
        
        logger.info("")
        logger.info("="*80)
        logger.info("REAL-TIME MONITOR STOPPED")
        logger.info("="*80)
        logger.info(f"  Total checks performed: {check_count}")
        logger.info(f"  Total orders processed: {total_orders_processed}")
        logger.info("  ✅ All processed data saved in batches/ and label/ folders")
        logger.info("="*80)
        logger.info("")


if __name__ == "__main__":
    main()

