"""
Production Runner for Multi-Account Order Processing

This script runs the order processing system in PRODUCTION mode.
- Uses production API endpoints (test_mode=False)
- Processes all active accounts
- Generates CSV files with correct shop names
- Uploads to SFTP
- Sends email notifications
"""

import logging
import sys

# Setup logging for production
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main production entry point"""
    logger.info("="*80)
    logger.info("PRODUCTION MODE - Multi-Account Order Processing")
    logger.info("="*80)
    logger.info("⚠️  Running in PRODUCTION mode - real orders will be processed!")
    logger.info("="*80)
    
    try:
        # Import required functions
        from multi_account_processor import process_account
        from config_manager import get_active_bol_accounts, get_config_summary
        
        # Get active accounts
        active_accounts = get_active_bol_accounts()
        config = get_config_summary()
        default_shop = config.get('default_shop', 'Trivium')
        
        if not active_accounts:
            logger.error("❌ No active Bol.com accounts found in configuration")
            logger.error("   Please check system_config.json and ensure at least one account has 'active': true")
            sys.exit(1)
        
        logger.info(f"Found {len(active_accounts)} active account(s):")
        for acc in active_accounts:
            logger.info(f"  - {acc['name']}")
        
        # Process all accounts in PRODUCTION mode (test_mode=False)
        results = []
        total_orders_all = 0
        
        for account in active_accounts:
            account_name = account['name']
            client_id = account['client_id']
            client_secret = account['client_secret']
            
            # Use account name as shop name
            shop_name = account_name if account_name in ['Trivium', 'Jean'] else default_shop
            
            logger.info("")
            logger.info(f"Processing account: {account_name} (Shop: {shop_name}) - PRODUCTION MODE")
            
            # Call process_account with test_mode=False for production
            from multi_account_processor import process_account
            result = process_account(
                account_name=account_name,
                client_id=client_id,
                client_secret=client_secret,
                shop_name=shop_name,
                test_mode=False  # PRODUCTION MODE
            )
            
            results.append(result)
            total_orders_all += result.get('processed', 0)
            
            if result.get('success'):
                logger.info(f"✅ Successfully processed {result.get('processed', 0)} orders for {account_name}")
            else:
                logger.error(f"❌ Failed to process account {account_name}: {result.get('error', 'Unknown error')}")
        
        # Final summary
        logger.info("")
        logger.info("="*80)
        logger.info("PRODUCTION PROCESSING COMPLETE")
        logger.info("="*80)
        logger.info(f"  Accounts processed: {len(results)}")
        logger.info(f"  Total orders processed: {total_orders_all}")
        logger.info("="*80)
        
        # Exit with error code if any account failed
        failed_accounts = [r for r in results if not r.get('success')]
        if failed_accounts:
            logger.error(f"⚠️  {len(failed_accounts)} account(s) failed to process")
            sys.exit(1)
        else:
            logger.info("✅ All accounts processed successfully")
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("")
        logger.info("⚠️  Processing interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Fatal error in production processing: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()

