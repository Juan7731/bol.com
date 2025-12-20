"""
Configuration Manager for Bol.com Order Processing System

Provides Python functions to manage configuration settings without UI.
Can be used by admin scripts or future UI implementations.
"""

import json
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration file path
CONFIG_FILE = "system_config.json"


def load_config() -> Dict:
    """
    Load configuration from JSON file.
    
    Returns:
        Dictionary with configuration settings
    """
    default_config = {
        "processing_times": ["08:00", "15:01", "", ""],
        "email": {
            "enabled": True,
            "smtp_host": "smtp.transip.email",
            "smtp_port": 465,
            "use_tls": False,
            "username": "info@trivium-ecommerce.com",
            "password": "juzge5-habkur-kidtoP",
            "from": "info@trivium-ecommerce.com",
            "recipients": [
                "finance@trivium-ecommerce.com",
                "constantijn@trivium-ecommerce.com",
                "info@trivium-ecommerce.com"
            ],
            "subject_template": "Bol.com orders summary: [total_orders] orders need to be processed",
            "body_template": "Today, [total_orders] orders need to be processed.\nThis number is based on the orders included in the generated Excel batch files."
        },
        "ftp": {
            "host": "triviu.ssh.transip.me",
            "port": 22,
            "username": "trivium-ecommercecom",
            "password": "&9z?8zcN&9z?8zcN",
            "remote_batch_dir": "/data/sites/web/trivium-ecommercecom/FTP/Batches",
            "remote_callback_dir": "/data/sites/web/trivium-ecommercecom/FTP/Callbacks"
        },
        "bol_accounts": [
            {
                "name": "Trivium",
                "client_id": "051dd4f6-c84e-4b98-876e-77a6727ca48a",
                "client_secret": "O@A58WI8CHfiGhf8JxQT72?oO5BYF)YfhsWTxNZB2BxTlxoxoHKY!IHsFuWb3YLH",
                "active": True
            },
            {
                "name": "Jean",
                "client_id": "f418eb2c-ca2c-4138-b5d3-fa89cb800dad",
                "client_secret": "rTj0Z!K1sZThWW!Rgu6u0t2@l62Z8jKXQDcNkx(QH0IX@m+cwiYnHpT4NNi42iVF",
                "active": False
            }
        ],
        "shop_mapping": {
            "default": "Trivium"
        }
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged = default_config.copy()
                merged.update(config)
                return merged
        except Exception as e:
            logger.error(f"Error loading config file: {e}. Using defaults.")
            return default_config
    else:
        # Create default config file
        save_config(default_config)
        return default_config


def save_config(config: Dict) -> bool:
    """
    Save configuration to JSON file.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"Configuration saved to {CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving config file: {e}")
        return False


def update_processing_times(times: List[str]) -> bool:
    """
    Update processing times (up to 4 time slots).
    
    Args:
        times: List of time strings in HH:MM format (24h), empty strings for unused slots
        
    Returns:
        True if successful, False otherwise
    """
    if len(times) > 4:
        logger.error("Maximum 4 processing times allowed")
        return False
    
    # Validate time format
    for time_str in times:
        if time_str and not _validate_time_format(time_str):
            logger.error(f"Invalid time format: {time_str}. Use HH:MM (24h)")
            return False
    
    config = load_config()
    config["processing_times"] = times[:4] + [""] * (4 - len(times))
    return save_config(config)


def update_email_settings(
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    from_address: str,
    recipients: List[str],
    use_tls: bool = False,
    subject_template: Optional[str] = None,
    body_template: Optional[str] = None
) -> bool:
    """
    Update email configuration settings.
    
    Args:
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port
        username: SMTP username
        password: SMTP password
        from_address: From email address
        recipients: List of recipient email addresses
        use_tls: Use TLS encryption
        subject_template: Email subject template (with [total_orders] placeholder)
        body_template: Email body template (with [total_orders] placeholder)
        
    Returns:
        True if successful, False otherwise
    """
    config = load_config()
    config["email"]["smtp_host"] = smtp_host
    config["email"]["smtp_port"] = smtp_port
    config["email"]["username"] = username
    config["email"]["password"] = password
    config["email"]["from"] = from_address
    config["email"]["recipients"] = recipients
    config["email"]["use_tls"] = use_tls
    
    if subject_template:
        config["email"]["subject_template"] = subject_template
    if body_template:
        config["email"]["body_template"] = body_template
    
    return save_config(config)


def update_ftp_settings(
    host: str,
    port: int,
    username: str,
    password: str,
    remote_batch_dir: Optional[str] = None,
    remote_callback_dir: Optional[str] = None
) -> bool:
    """
    Update FTP/SFTP configuration settings.
    
    Args:
        host: SFTP hostname
        port: SFTP port
        username: SFTP username
        password: SFTP password
        remote_batch_dir: Remote directory for batch uploads
        remote_callback_dir: Remote directory for callback files
        
    Returns:
        True if successful, False otherwise
    """
    config = load_config()
    config["ftp"]["host"] = host
    config["ftp"]["port"] = port
    config["ftp"]["username"] = username
    config["ftp"]["password"] = password
    
    if remote_batch_dir:
        config["ftp"]["remote_batch_dir"] = remote_batch_dir
    if remote_callback_dir:
        config["ftp"]["remote_callback_dir"] = remote_callback_dir
    
    return save_config(config)


def add_bol_account(name: str, client_id: str, client_secret: str, active: bool = False) -> bool:
    """
    Add a new Bol.com account.
    
    Args:
        name: Account name (e.g., "Trivium", "Jean")
        client_id: Bol.com client ID
        client_secret: Bol.com client secret
        active: Whether this account is active
        
    Returns:
        True if successful, False otherwise
    """
    config = load_config()
    
    # Check if account already exists
    for account in config["bol_accounts"]:
        if account["name"] == name:
            logger.warning(f"Account '{name}' already exists. Use update_bol_account() instead.")
            return False
    
    config["bol_accounts"].append({
        "name": name,
        "client_id": client_id,
        "client_secret": client_secret,
        "active": active
    })
    
    return save_config(config)


def update_bol_account(name: str, client_id: Optional[str] = None, 
                       client_secret: Optional[str] = None, 
                       active: Optional[bool] = None) -> bool:
    """
    Update an existing Bol.com account.
    
    Args:
        name: Account name to update
        client_id: New client ID (optional)
        client_secret: New client secret (optional)
        active: Active status (optional)
        
    Returns:
        True if successful, False otherwise
    """
    config = load_config()
    
    for account in config["bol_accounts"]:
        if account["name"] == name:
            if client_id:
                account["client_id"] = client_id
            if client_secret:
                account["client_secret"] = client_secret
            if active is not None:
                account["active"] = active
            return save_config(config)
    
    logger.error(f"Account '{name}' not found")
    return False


def get_active_bol_accounts() -> List[Dict]:
    """
    Get all active Bol.com accounts.
    
    Returns:
        List of active account dictionaries
    """
    config = load_config()
    return [acc for acc in config["bol_accounts"] if acc.get("active", False)]


def set_default_shop(shop_name: str) -> bool:
    """
    Set default shop name for orders.
    
    Args:
        shop_name: Shop name (e.g., "Trivium", "Jean")
        
    Returns:
        True if successful, False otherwise
    """
    config = load_config()
    config["shop_mapping"]["default"] = shop_name
    return save_config(config)


def _validate_time_format(time_str: str) -> bool:
    """
    Validate time format (HH:MM 24h).
    
    Args:
        time_str: Time string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not time_str:
        return True  # Empty string is valid (unused slot)
    
    try:
        parts = time_str.split(':')
        if len(parts) != 2:
            return False
        hour = int(parts[0])
        minute = int(parts[1])
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except (ValueError, AttributeError):
        return False


def get_config_summary() -> Dict:
    """
    Get a summary of current configuration (without sensitive data).
    
    Returns:
        Dictionary with configuration summary
    """
    config = load_config()
    
    return {
        "processing_times": config["processing_times"],
        "email": {
            "enabled": config["email"]["enabled"],
            "smtp_host": config["email"]["smtp_host"],
            "smtp_port": config["email"]["smtp_port"],
            "from": config["email"]["from"],
            "recipients_count": len(config["email"]["recipients"])
        },
        "ftp": {
            "host": config["ftp"]["host"],
            "port": config["ftp"]["port"],
            "username": config["ftp"]["username"]
        },
        "bol_accounts": [
            {
                "name": acc["name"],
                "active": acc.get("active", False)
            }
            for acc in config["bol_accounts"]
        ],
        "default_shop": config["shop_mapping"]["default"]
    }


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Example usage
    print("Configuration Manager - Example Usage")
    print("="*80)
    
    # Load config
    config = load_config()
    print(f"Loaded configuration: {len(config['bol_accounts'])} Bol.com accounts")
    
    # Get summary
    summary = get_config_summary()
    print(f"\nConfiguration Summary:")
    print(f"  Processing times: {summary['processing_times']}")
    print(f"  Email recipients: {summary['email']['recipients_count']}")
    print(f"  Active Bol accounts: {len([a for a in summary['bol_accounts'] if a['active']])}")
    print(f"  Default shop: {summary['default_shop']}")

