"""
Scheduler for Status Callback Handler

Runs the callback processor periodically (e.g., once per minute via cron).
"""

import logging
import time
import sys
from status_callback_handler import run_callback_processor

logger = logging.getLogger(__name__)


def run_continuous(interval_seconds: int = 60) -> None:
    """
    Run callback processor continuously with specified interval.
    
    Args:
        interval_seconds: Interval between runs in seconds (default: 60 = 1 minute)
    """
    logger.info("="*80)
    logger.info("STATUS CALLBACK SCHEDULER - CONTINUOUS MODE")
    logger.info(f"Checking for callback files every {interval_seconds} seconds")
    logger.info("Press Ctrl+C to stop")
    logger.info("="*80)
    
    try:
        while True:
            try:
                run_callback_processor()
            except Exception as e:
                logger.error(f"Error in callback processor: {e}")
            
            # Wait for next interval
            logger.debug(f"Waiting {interval_seconds} seconds until next check...")
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        logger.info("\nScheduler stopped by user.")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        # Run continuously (for testing)
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        run_continuous(interval)
    else:
        # Run once (for cron job)
        run_callback_processor()

