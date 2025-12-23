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


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global running
    logger.info("")
    logger.info("⚠️  Shutdown signal received. Stopping monitor...")
    running = False


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


def process_orders_realtime() -> Dict:
    """
    Process orders from all active accounts in real-time.
    Returns processing results.
    """
    try:
        from multi_account_processor import process_account
        from config_manager import get_active_bol_accounts, get_config_summary
        
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
            
            # Use account name as shop name
            shop_name = account_name if account_name in ['Trivium', 'Jean'] else default_shop
            
            logger.info(f"Checking account: {account_name} (Shop: {shop_name})")
            
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
            
            if orders_processed > 0:
                logger.info(f"✅ Processed {orders_processed} order(s) for {account_name}")
            else:
                logger.info(f"ℹ️  No new orders for {account_name}")
        
        return {
            'accounts_processed': len(results),
            'total_orders': total_orders_all,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error processing orders: {e}")
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
    
    logger.info("⌨️  Press Ctrl+C to stop")
    logger.info("="*80)
    logger.info("")
    
    check_count = 0
    total_orders_processed = 0
    last_scheduled_run: Dict[str, date] = {}  # time_str -> date when last run at scheduled time
    
    try:
        while running:
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
            total_orders_processed += orders_this_check
            
            # Summary for this check
            if should_force_process:
                if orders_this_check > 0:
                    logger.info("")
                    logger.info(f"✅ Scheduled check #{check_count} complete: {orders_this_check} order(s) processed")
                else:
                    logger.info("")
                    logger.info(f"✅ Scheduled check #{check_count} complete: No new orders (scheduled run completed)")
            else:
                if orders_this_check > 0:
                    logger.info("")
                    logger.info(f"✅ Check #{check_count} complete: {orders_this_check} order(s) processed")
                else:
                    logger.info("")
                    logger.info(f"ℹ️  Check #{check_count} complete: No new orders")
            
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
            if running:
                logger.info("")
                logger.info(f"⏳ Next check in 60 seconds... (Ctrl+C to stop)")
                
                # Sleep in 1-second intervals to check for shutdown signal
                for i in range(60):
                    if not running:
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
        logger.info("")
        logger.info("="*80)
        logger.info("REAL-TIME MONITOR STOPPED")
        logger.info("="*80)
        logger.info(f"  Total checks performed: {check_count}")
        logger.info(f"  Total orders processed: {total_orders_processed}")
        logger.info("="*80)
        logger.info("")


if __name__ == "__main__":
    main()

