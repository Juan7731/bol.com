"""
Scheduler script for Bol.com order processing
Runs continuously and processes orders at configured times (default: 08:00 and 15:01)

Usage:
    python run_scheduler.py
    
Or run as a Windows service / Linux daemon
"""

import logging
from order_processing import run_scheduler

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    print("="*80)
    print("Bol.com Order Processing Scheduler")
    print("="*80)
    print("\nThis script will run continuously and process orders at configured times.")
    print("Press Ctrl+C to stop.\n")
    
    try:
        run_scheduler()
    except KeyboardInterrupt:
        print("\n\nScheduler stopped by user.")
    except Exception as e:
        logging.error(f"Scheduler error: {e}", exc_info=True)
        raise

