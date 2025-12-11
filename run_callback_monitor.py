"""
Continuous Callback Monitor
Monitors FTP/Callbacks directory every minute and processes status files automatically
"""

import time
import logging
from datetime import datetime
from status_callback_handler import process_callback_files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_continuous_monitor(check_interval: int = 60):
    """
    Run the callback monitor continuously, checking every interval.
    
    Args:
        check_interval: Time in seconds between checks (default: 60 = 1 minute)
    """
    logger.info("="*80)
    logger.info("BOL.COM CALLBACK MONITOR - CONTINUOUS MODE")
    logger.info("="*80)
    logger.info(f"Monitoring FTP/Callbacks directory")
    logger.info(f"Check interval: {check_interval} seconds ({check_interval//60} minute(s))")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    logger.info("\n🔍 Monitor started. Press Ctrl+C to stop.\n")
    
    cycle_count = 0
    total_stats = {
        'total_processed': 0,
        'total_updated': 0,
        'total_labels_deleted': 0,
        'total_ignored': 0,
        'total_errors': 0
    }
    
    try:
        while True:
            cycle_count += 1
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info(f"\n{'='*80}")
            logger.info(f"⏰ Check #{cycle_count} at {timestamp}")
            logger.info(f"{'='*80}")
            
            try:
                # Process callback files
                stats = process_callback_files()
                
                # Update totals
                total_stats['total_processed'] += stats['processed']
                total_stats['total_updated'] += stats['updated']
                total_stats['total_labels_deleted'] += stats.get('labels_deleted', 0)
                total_stats['total_ignored'] += stats['ignored']
                total_stats['total_errors'] += stats['errors']
                
                # Log results
                if stats['processed'] > 0:
                    logger.info(f"\n📊 Cycle #{cycle_count} Results:")
                    logger.info(f"   Files processed: {stats['processed']}")
                    logger.info(f"   Orders updated: {stats['updated']}")
                    logger.info(f"   Labels deleted: {stats.get('labels_deleted', 0)}")
                    logger.info(f"   Ignored: {stats['ignored']}")
                    logger.info(f"   Errors: {stats['errors']}")
                else:
                    logger.info("   No callback files found")
                
            except Exception as e:
                logger.error(f"❌ Error during cycle #{cycle_count}: {e}")
                import traceback
                traceback.print_exc()
            
            # Show cumulative stats
            logger.info(f"\n📈 Cumulative Totals (since start):")
            logger.info(f"   Total files: {total_stats['total_processed']}")
            logger.info(f"   Total orders updated: {total_stats['total_updated']}")
            logger.info(f"   Total labels deleted: {total_stats['total_labels_deleted']}")
            logger.info(f"   Total ignored: {total_stats['total_ignored']}")
            logger.info(f"   Total errors: {total_stats['total_errors']}")
            
            # Wait for next check
            next_check = datetime.now()
            next_check = next_check.replace(second=0, microsecond=0)
            from datetime import timedelta
            next_check = next_check + timedelta(seconds=check_interval)
            
            logger.info(f"\n⏳ Next check at: {next_check.strftime('%H:%M:%S')}")
            logger.info(f"{'='*80}\n")
            
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        logger.info("\n\n" + "="*80)
        logger.info("🛑 Monitor stopped by user")
        logger.info("="*80)
        logger.info(f"\nFinal Statistics:")
        logger.info(f"  Total checks performed: {cycle_count}")
        logger.info(f"  Total files processed: {total_stats['total_processed']}")
        logger.info(f"  Total orders updated: {total_stats['total_updated']}")
        logger.info(f"  Total labels deleted: {total_stats['total_labels_deleted']}")
        logger.info(f"  Total ignored: {total_stats['total_ignored']}")
        logger.info(f"  Total errors: {total_stats['total_errors']}")
        logger.info("="*80)


def run_single_check():
    """
    Run a single callback check (for testing or manual execution).
    """
    logger.info("="*80)
    logger.info("BOL.COM CALLBACK MONITOR - SINGLE CHECK MODE")
    logger.info("="*80)
    
    try:
        stats = process_callback_files()
        
        logger.info("\n📊 Results:")
        logger.info(f"   Files processed: {stats['processed']}")
        logger.info(f"   Orders updated: {stats['updated']}")
        logger.info(f"   Labels deleted: {stats.get('labels_deleted', 0)}")
        logger.info(f"   Ignored: {stats['ignored']}")
        logger.info(f"   Errors: {stats['errors']}")
        logger.info("="*80)
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error during check: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "once":
            # Run single check
            run_single_check()
        elif command == "monitor":
            # Run continuous monitor
            interval = 60  # Default: 1 minute
            if len(sys.argv) > 2:
                try:
                    interval = int(sys.argv[2])
                except ValueError:
                    print("Invalid interval. Using default: 60 seconds")
            run_continuous_monitor(check_interval=interval)
        else:
            print("Unknown command. Available commands:")
            print("  once           - Run a single check")
            print("  monitor [secs] - Run continuous monitoring (default: 60 seconds)")
    else:
        # Default: run continuous monitor every minute
        run_continuous_monitor(check_interval=60)

