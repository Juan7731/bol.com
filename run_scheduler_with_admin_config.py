"""
Enhanced Scheduler with Admin Panel Configuration
Uses configuration from the admin panel to schedule order processing
"""

import schedule
import time
import logging
from datetime import datetime
from admin_config_reader import AdminConfigReader
from order_processing import process_all_orders

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_orders_if_enabled():
    """Process orders only if enabled for today"""
    config = AdminConfigReader()
    
    if config.is_processing_enabled_today():
        logger.info("📅 Processing enabled for today - Running order processing...")
        try:
            process_all_orders()
            logger.info("✅ Order processing completed successfully")
        except Exception as e:
            logger.error(f"❌ Error during order processing: {e}")
            import traceback
            traceback.print_exc()
    else:
        today = datetime.now().strftime('%A')
        logger.info(f"⏸️  Processing disabled for {today} - Skipping")


def setup_scheduler():
    """Setup scheduler with times from admin configuration"""
    config = AdminConfigReader()
    processing_times = config.get_processing_times()
    weekly_schedule = config.get_weekly_schedule()
    
    logger.info("="*80)
    logger.info("SCHEDULER SETUP WITH ADMIN CONFIGURATION")
    logger.info("="*80)
    
    logger.info("\n⏰ Processing Times:")
    if processing_times:
        for i, time_str in enumerate(processing_times, 1):
            logger.info(f"  {i}. {time_str}")
            schedule.every().day.at(time_str).do(process_orders_if_enabled)
    else:
        logger.warning("  ⚠️  No processing times configured!")
    
    logger.info("\n📅 Weekly Schedule:")
    enabled_days = [day.capitalize() for day, enabled in weekly_schedule.items() if enabled]
    disabled_days = [day.capitalize() for day, enabled in weekly_schedule.items() if not enabled]
    
    if enabled_days:
        logger.info(f"  ✅ Enabled:  {', '.join(enabled_days)}")
    if disabled_days:
        logger.info(f"  ❌ Disabled: {', '.join(disabled_days)}")
    
    # Show next scheduled run
    next_day, next_time = config.get_next_processing_time()
    if next_day and next_time:
        logger.info(f"\n⏰ Next scheduled processing: {next_day} at {next_time}")
    else:
        logger.info("\n⏰ No processing scheduled")
    
    logger.info("="*80)
    logger.info("\n🔍 Scheduler started. Press Ctrl+C to stop.\n")


def run_scheduler():
    """Run the scheduler continuously"""
    setup_scheduler()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
            # Reload configuration every hour to pick up admin changes
            current_minute = datetime.now().minute
            if current_minute == 0:
                logger.info("🔄 Reloading configuration from admin panel...")
                schedule.clear()
                setup_scheduler()
                
    except KeyboardInterrupt:
        logger.info("\n\n" + "="*80)
        logger.info("🛑 Scheduler stopped by user")
        logger.info("="*80)


if __name__ == "__main__":
    run_scheduler()

