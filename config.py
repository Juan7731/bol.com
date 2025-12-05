"""
Configuration file for Bol.com API credentials
Keep this file secure and do not commit credentials to version control
"""

# Bol.com API Credentials
BOL_CLIENT_ID = "051dd4f6-c84e-4b98-876e-77a6727ca48a"
BOL_CLIENT_SECRET = "O@A58WI8CHfiGhf8JxQT72?oO5BYF)YfhsWTxNZB2BxTlxoxoHKY!IHsFuWb3YLH"

# Environment settings
TEST_MODE = True  # Set to False for production

# API Settings
API_TIMEOUT = 30  # Request timeout in seconds
MAX_RETRIES = 3   # Maximum number of retry attempts

# Processing times (up to four per day, HH:MM 24h format)
# Defaults: 08:00 and 15:01
PROCESS_TIMES = [
    "08:00",
    "15:01",
    "",      # optional slot 3
    "",      # optional slot 4
]

# Local directory where Excel batches are stored
LOCAL_BATCH_DIR = "batches"

# SFTP settings (from project description)
SFTP_HOST = "triviu.ssh.transip.me"
SFTP_PORT = 22
SFTP_USERNAME = "trivium-ecommercecom"
SFTP_PASSWORD = "&9z?8zcN&9z?8zcN"
SFTP_REMOTE_BATCH_DIR = "/data/sites/web/trivium-ecommercecom/FTP/Batches"

# Email settings (from client)
EMAIL_ENABLED = True
EMAIL_SMTP_HOST = "smtp.transip.email"
EMAIL_SMTP_PORT = 465
EMAIL_USE_TLS = False  # using SSL on port 465 instead of STARTTLS
EMAIL_USERNAME = "info@trivium-ecommerce.com"
EMAIL_PASSWORD = "juzge5-habkur-kidtoP"
EMAIL_FROM = "info@trivium-ecommerce.com"
EMAIL_RECIPIENTS = [
    "finance@trivium-ecommerce.com",
    "constantijn@trivium-ecommerce.com",
    "info@trivium-ecommerce.com",
]

# Email templates (use [total_orders] placeholder)
EMAIL_SUBJECT_TEMPLATE = "Bol.com orders summary: [total_orders] orders need to be processed"
EMAIL_BODY_TEMPLATE = (
    "Today, [total_orders] orders need to be processed.\n"
    "This number is based on the orders included in the generated Excel batch files."
)

# Shop configuration
# Set to "Jean" or "Trivium" to indicate which shop orders come from
# For multiple shops, you can map order IDs or use different configs per shop
DEFAULT_SHOP_NAME = "Trivium"  # Default shop name for orders


