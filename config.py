"""
Configuration file for Bol.com API credentials
Keep this file secure and do not commit credentials to version control
"""

# Bol.com API Credentials - Jean Shop
# Note: This is Jean's account. For Trivium, use multi_account_processor.py
BOL_CLIENT_ID = "051dd4f6-c84e-4b98-876e-77a6727ca48a"  # Jean
BOL_CLIENT_SECRET = "O@A58WI8CHfiGhf8JxQT72?oO5BYF)YfhsWTxNZB2BxTlxoxoHKY!IHsFuWb3YLH"  # Jean

# Environment settings
TEST_MODE = False  # Set to False for production

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

# Local directory where CSV batches are stored
LOCAL_BATCH_DIR = "batches"

# Local directory where shipping label PDFs are stored
LOCAL_LABEL_DIR = "label"

# SFTP settings (from project description)
SFTP_HOST = "triviu.ssh.transip.me"
SFTP_PORT = 22
SFTP_USERNAME = "trivium-ecommercecom"
SFTP_PASSWORD = "&9z?8zcN&9z?8zcN"
SFTP_REMOTE_BATCH_DIR = "/data/sites/web/trivium-ecommercecom/FTP/Batches"
SFTP_REMOTE_LABEL_DIR = "/data/sites/web/trivium-ecommercecom/FTP/Label"

# Email settings (from client)
EMAIL_ENABLED = True
EMAIL_SMTP_HOST = "smtp.transip.email"
EMAIL_SMTP_PORT = 587  # Use port 587 for STARTTLS instead of 465 for SSL
EMAIL_USE_TLS = True  # Use STARTTLS on port 587
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
    "This number is based on the orders included in the generated CSV batch files."
)

# Shop configuration
# Set to "Jean" or "Trivium" to indicate which shop orders come from
# IMPORTANT: This MUST match the credentials above!
# Current credentials are for JEAN, so shop name is JEAN
DEFAULT_SHOP_NAME = "Jean"  # Default shop name for orders (matches credentials above)


