"""
Status Callback Handler for Bol.com Orders

Monitors FTP directory for HTML status files and updates Bol.com orders when "verzonden" is detected.
"""

import os
import re
import logging
import paramiko
from typing import List, Dict, Optional
from datetime import datetime

from bol_api_client import BolAPIClient
from config import (
    BOL_CLIENT_ID,
    BOL_CLIENT_SECRET,
    TEST_MODE,
    SFTP_HOST,
    SFTP_PORT,
    SFTP_USERNAME,
    SFTP_PASSWORD,
)

logger = logging.getLogger(__name__)

# FTP Callback directory
SFTP_CALLBACK_DIR = "/data/sites/web/trivium-ecommercecom/FTP/Callbacks"


def parse_html_status_file(html_content: str) -> Optional[Dict[str, str]]:
    """
    Parse HTML status file to extract order ID and status.
    
    Expected format: HTML file containing Bol.com order ID and status ("verzonden" or "niet verzonden")
    
    Args:
        html_content: HTML file content as string
        
    Returns:
        Dictionary with 'order_id' and 'status', or None if parsing fails
    """
    try:
        # Look for order ID (Bol.com order IDs are typically alphanumeric, e.g., "A000C2F77M")
        # Pattern: Look for common order ID patterns
        order_id_patterns = [
            r'order[_\s-]?id["\']?\s*[:=]\s*["\']?([A-Z0-9]{10,})',  # order_id: "A000C2F77M"
            r'order["\']?\s*[:=]\s*["\']?([A-Z0-9]{10,})',  # order: "A000C2F77M"
            r'<[^>]*>([A-Z0-9]{10,})</',  # <td>A000C2F77M</td>
            r'([A-Z0-9]{10,})',  # Just find any 10+ char alphanumeric (fallback)
        ]
        
        order_id = None
        for pattern in order_id_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                order_id = match.group(1)
                break
        
        # Look for status
        status = None
        if 'verzonden' in html_content.lower():
            status = 'verzonden'
        elif 'niet verzonden' in html_content.lower():
            status = 'niet verzonden'
        
        if order_id and status:
            return {
                'order_id': order_id,
                'status': status
            }
        
        logger.warning(f"Could not parse HTML file. Order ID: {order_id}, Status: {status}")
        return None
        
    except Exception as e:
        logger.error(f"Error parsing HTML file: {e}")
        return None


def get_shipment_id_for_order(client: BolAPIClient, order_id: str) -> Optional[str]:
    """
    Get shipment ID for a given order ID.
    
    Args:
        client: Bol.com API client
        order_id: Bol.com order ID
        
    Returns:
        Shipment ID if found, None otherwise
    """
    try:
        # Get shipments for this order
        # Note: get_shipments may need order_id as parameter or we may need to get order first
        try:
            shipments_response = client.get_shipments(order_id=order_id)
        except TypeError:
            # If get_shipments doesn't accept order_id, try without it and filter
            shipments_response = client.get_shipments()
            # Filter by order_id if response contains order information
            shipments = shipments_response.get('shipments', [])
            shipments = [s for s in shipments if s.get('orderId') == order_id]
            shipments_response = {'shipments': shipments}
        
        shipments = shipments_response.get('shipments', [])
        
        if shipments:
            # Get the most recent shipment (first one)
            shipment_id = shipments[0].get('shipmentId')
            logger.info(f"Found shipment {shipment_id} for order {order_id}")
            return shipment_id
        
        logger.warning(f"No shipments found for order {order_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error getting shipment for order {order_id}: {e}")
        return None


def update_order_status_shipped(client: BolAPIClient, order_id: str) -> bool:
    """
    Update Bol.com order status to shipped.
    
    Args:
        client: Bol.com API client
        order_id: Bol.com order ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # First, get the shipment ID for this order
        shipment_id = get_shipment_id_for_order(client, order_id)
        
        if not shipment_id:
            logger.warning(f"Cannot update order {order_id}: No shipment found")
            return False
        
        # Update shipment status
        # For "verzenden via bol", we typically don't need transporter code
        # But we can mark it as shipped
        try:
            client.update_shipment(shipment_id)
            logger.info(f"✅ Successfully updated order {order_id} (shipment {shipment_id}) to shipped")
            return True
        except Exception as e:
            logger.error(f"Error updating shipment {shipment_id}: {e}")
            # Try alternative: create shipment update event
            # Some APIs require creating a shipment update rather than updating existing
            return False
            
    except Exception as e:
        logger.error(f"Error updating order {order_id} status: {e}")
        return False


def fetch_callback_files_sftp() -> List[Dict[str, str]]:
    """
    Fetch HTML status files from SFTP callback directory.
    
    Returns:
        List of dictionaries with 'filename' and 'content' keys
    """
    files = []
    transport = None
    sftp = None
    
    try:
        # Create transport with timeout settings
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.banner_timeout = 30  # Increase banner timeout
        transport.auth_timeout = 30    # Increase auth timeout
        
        # Connect with credentials
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        try:
            # List files in callback directory
            try:
                file_list = sftp.listdir(SFTP_CALLBACK_DIR)
            except FileNotFoundError:
                logger.warning(f"Callback directory not found: {SFTP_CALLBACK_DIR}")
                return files
            
            # Filter for HTML files
            html_files = [f for f in file_list if f.lower().endswith('.html')]
            
            logger.info(f"Found {len(html_files)} HTML files in callback directory")
            
            # Read each HTML file
            for filename in html_files:
                try:
                    remote_path = f"{SFTP_CALLBACK_DIR}/{filename}"
                    with sftp.open(remote_path, 'r') as f:
                        content = f.read().decode('utf-8', errors='ignore')
                        files.append({
                            'filename': filename,
                            'content': content,
                            'remote_path': remote_path
                        })
                        logger.debug(f"Read file: {filename} ({len(content)} bytes)")
                except Exception as e:
                    logger.error(f"Error reading file {filename}: {e}")
            
        finally:
            # Ensure connections are properly closed
            if sftp:
                try:
                    sftp.close()
                except:
                    pass
            if transport:
                try:
                    transport.close()
                except:
                    pass
            
    except Exception as e:
        logger.error(f"Error connecting to SFTP for callbacks: {e}")
        # Clean up on error
        if sftp:
            try:
                sftp.close()
            except:
                pass
        if transport:
            try:
                transport.close()
            except:
                pass
    
    return files


def process_callback_files() -> Dict[str, int]:
    """
    Process all callback files from FTP and update Bol.com orders.
    
    Returns:
        Dictionary with processing statistics:
        - processed: Number of files processed
        - updated: Number of orders successfully updated
        - errors: Number of errors
        - ignored: Number of files with "niet verzonden"
    """
    stats = {
        'processed': 0,
        'updated': 0,
        'errors': 0,
        'ignored': 0
    }
    
    logger.info("Starting callback file processing...")
    
    # Fetch HTML files from SFTP
    html_files = fetch_callback_files_sftp()
    
    if not html_files:
        logger.info("No callback files found")
        return stats
    
    # Initialize Bol.com API client
    client = BolAPIClient(BOL_CLIENT_ID, BOL_CLIENT_SECRET, test_mode=TEST_MODE)
    
    # Process each file
    processed_files = []
    
    for file_info in html_files:
        filename = file_info['filename']
        content = file_info['content']
        remote_path = file_info['remote_path']
        
        stats['processed'] += 1
        
        try:
            # Parse HTML file
            parsed = parse_html_status_file(content)
            
            if not parsed:
                logger.warning(f"Could not parse file {filename}")
                stats['errors'] += 1
                continue
            
            order_id = parsed['order_id']
            status = parsed['status']
            
            logger.info(f"File {filename}: Order {order_id}, Status: {status}")
            
            if status == 'niet verzonden':
                logger.info(f"Ignoring order {order_id} (not shipped)")
                stats['ignored'] += 1
                processed_files.append(remote_path)
                continue
            
            if status == 'verzonden':
                # Update order status in Bol.com
                success = update_order_status_shipped(client, order_id)
                
                if success:
                    stats['updated'] += 1
                    processed_files.append(remote_path)
                    logger.info(f"✅ Successfully processed order {order_id} from {filename}")
                else:
                    stats['errors'] += 1
                    logger.error(f"❌ Failed to update order {order_id} from {filename}")
            else:
                logger.warning(f"Unknown status '{status}' in file {filename}")
                stats['errors'] += 1
                
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            stats['errors'] += 1
    
    # Archive/delete processed files (optional - move to processed folder)
    if processed_files:
        archive_processed_files(processed_files)
    
    logger.info(f"Callback processing complete: {stats}")
    return stats


def archive_processed_files(file_paths: List[str]) -> None:
    """
    Archive processed callback files (move to processed folder or delete).
    
    Args:
        file_paths: List of remote file paths to archive
    """
    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.banner_timeout = 30  # Increase banner timeout
        transport.auth_timeout = 30    # Increase auth timeout
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        try:
            # Create processed directory if it doesn't exist
            processed_dir = f"{SFTP_CALLBACK_DIR}/processed"
            try:
                sftp.mkdir(processed_dir)
            except IOError:
                pass  # Directory already exists
            
            # Move files to processed directory
            for remote_path in file_paths:
                try:
                    filename = os.path.basename(remote_path)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    new_filename = f"{timestamp}_{filename}"
                    new_path = f"{processed_dir}/{new_filename}"
                    
                    sftp.rename(remote_path, new_path)
                    logger.debug(f"Archived {filename} to {new_path}")
                except Exception as e:
                    logger.warning(f"Could not archive {remote_path}: {e}")
                    # Try to delete instead
                    try:
                        sftp.remove(remote_path)
                        logger.debug(f"Deleted {remote_path}")
                    except Exception as e2:
                        logger.error(f"Could not delete {remote_path}: {e2}")
        
        finally:
            sftp.close()
            transport.close()
            
    except Exception as e:
        logger.error(f"Error archiving processed files: {e}")


def run_callback_processor() -> None:
    """
    Main function to run the callback processor.
    This should be called via cron job or scheduler (e.g., once per minute).
    """
    logger.info("="*80)
    logger.info("BOL.COM STATUS CALLBACK PROCESSOR")
    logger.info("="*80)
    
    stats = process_callback_files()
    
    logger.info("="*80)
    logger.info(f"Processing Summary:")
    logger.info(f"  Files processed: {stats['processed']}")
    logger.info(f"  Orders updated: {stats['updated']}")
    logger.info(f"  Ignored (niet verzonden): {stats['ignored']}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info("="*80)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Run callback processor
    run_callback_processor()

