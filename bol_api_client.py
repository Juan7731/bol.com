"""
Bol.com Retailer API v10 Client
Handles OAuth 2.0 authentication and API requests
"""

import requests
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BolAPIClient:
    """
    Client for Bol.com Retailer API v10
    Handles OAuth 2.0 authentication and provides methods to interact with the API
    """
    
    # API endpoints
    OAUTH_TOKEN_URL = "https://login.bol.com/token"
    API_BASE_URL = "https://api.bol.com/retailer"
    
    def __init__(self, client_id: str, client_secret: str, test_mode: bool = True):
        """
        Initialize the Bol.com API client
        
        Args:
            client_id: Bol.com client ID
            client_secret: Bol.com client secret
            test_mode: If True, uses test environment (default: True)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.test_mode = test_mode
        
        # Token management
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.token_type: str = "Bearer"
        
        # Session for connection pooling
        self.session = requests.Session()
        
    def _get_access_token(self) -> str:
        """
        Obtain or refresh OAuth 2.0 access token
        
        Returns:
            Access token string
            
        Raises:
            Exception: If authentication fails
        """
        # Check if we have a valid token
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at - timedelta(minutes=5):
                # Token is still valid (with 5 minute buffer)
                return self.access_token
        
        # Request new token
        logger.info("Requesting new access token from Bol.com...")
        
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = self.session.post(
                self.OAUTH_TOKEN_URL,
                data=auth_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)  # Default to 1 hour
            
            # Calculate expiration time
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            self.token_type = token_data.get('token_type', 'Bearer')
            
            logger.info(f"Successfully obtained access token (expires in {expires_in}s)")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to obtain access token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise Exception(f"Authentication failed: {e}")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for API requests including authorization
        
        Returns:
            Dictionary of headers
        """
        token = self._get_access_token()
        headers = {
            'Authorization': f'{self.token_type} {token}',
            'Accept': 'application/vnd.retailer.v10+json',
            'Content-Type': 'application/vnd.retailer.v10+json'
        }
        return headers
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an API request with automatic token refresh
        
        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            endpoint: API endpoint (relative to base URL)
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            JSON response as dictionary
            
        Raises:
            Exception: If request fails
        """
        url = f"{self.API_BASE_URL}{endpoint}"
        headers = self._get_headers()
        
        # Merge headers
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"API request failed: {method} {url}")
            logger.error(f"Status: {e.response.status_code}")
            logger.error(f"Response: {e.response.text}")
            
            # If unauthorized, try refreshing token once
            if e.response.status_code == 401:
                logger.info("Received 401, refreshing token and retrying...")
                self.access_token = None  # Force token refresh
                headers = self._get_headers()
                kwargs['headers'] = headers
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            
            raise Exception(f"API request failed: {e}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            raise Exception(f"Request failed: {e}")
    
    def get_orders(self, status: str = "OPEN", page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """
        Retrieve orders from Bol.com
        
        Args:
            status: Order status filter (OPEN, SHIPPED, CANCELLED, etc.)
            page: Page number (default: 1)
            limit: Number of orders per page (default: 100, max: 250)
            
        Returns:
            Dictionary containing orders data
        """
        endpoint = "/orders"
        params = {
            'status': status,
            'page': page,
            'limit': min(limit, 250)  # API max is 250
        }
        
        logger.info(f"Fetching orders with status '{status}' (page {page})...")
        return self._make_request('GET', endpoint, params=params)
    
    def get_all_open_orders(self) -> List[Dict[str, Any]]:
        """
        Retrieve all open orders (handles pagination automatically)
        
        Returns:
            List of all open orders
        """
        all_orders = []
        page = 1
        limit = 250  # Use max limit for efficiency
        
        while True:
            response = self.get_orders(status="OPEN", page=page, limit=limit)
            orders = response.get('orders', [])
            
            if not orders:
                break
                
            all_orders.extend(orders)
            
            # Check if there are more pages
            total_pages = response.get('pagination', {}).get('totalPages', 1)
            if page >= total_pages:
                break
                
            page += 1
        
        logger.info(f"Retrieved {len(all_orders)} open orders")
        return all_orders
    
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific order by ID
        
        Args:
            order_id: Bol.com order ID
            
        Returns:
            Order data dictionary
        """
        endpoint = f"/orders/{order_id}"
        logger.info(f"Fetching order {order_id}...")
        return self._make_request('GET', endpoint)
    
    def get_shipment(self, shipment_id: str) -> Dict[str, Any]:
        """
        Retrieve shipment information
        
        Args:
            shipment_id: Shipment ID
            
        Returns:
            Shipment data dictionary
        """
        endpoint = f"/shipments/{shipment_id}"
        logger.info(f"Fetching shipment {shipment_id}...")
        return self._make_request('GET', endpoint)
    
    def get_shipments(self, order_id: Optional[str] = None, 
                     page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """
        Retrieve shipments
        
        Args:
            order_id: Optional order ID to filter shipments
            page: Page number
            limit: Number of shipments per page
            
        Returns:
            Dictionary containing shipments data
        """
        endpoint = "/shipments"
        params = {
            'page': page,
            'limit': min(limit, 250)
        }
        
        if order_id:
            params['order-id'] = order_id
        
        logger.info(f"Fetching shipments (page {page})...")
        return self._make_request('GET', endpoint, params=params)
    
    def get_delivery_options(self, order_item_id: str, quantity: int = 1) -> Dict[str, Any]:
        """
        Get available delivery options (shipping label offers) for an order item
        
        Args:
            order_item_id: Order item ID
            quantity: Quantity for the order item (default: 1)
            
        Returns:
            Dictionary containing available delivery options with shippingLabelOfferId
        """
        endpoint = "/shipping-labels/delivery-options"
        payload = {
            'orderItems': [
                {
                    'orderItemId': order_item_id,
                    'quantity': quantity
                }
            ]
        }
        logger.info(f"🔍 Fetching delivery options for order item {order_item_id} (quantity: {quantity})...")
        logger.info(f"📦 Payload: {payload}")
        try:
            response = self._make_request('POST', endpoint, json=payload)
            logger.info(f"✅ Delivery options response keys: {list(response.keys())}")
            delivery_options = response.get('deliveryOptions', [])
            logger.info(f"✅ Found {len(delivery_options)} delivery options")
            if delivery_options:
                for idx, option in enumerate(delivery_options):
                    logger.info(f"   Option {idx + 1}: {option.get('labelDisplayName', 'N/A')} (ID: {option.get('shippingLabelOfferId', 'N/A')})")
            return response
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Could not fetch delivery options: {error_msg}")
            logger.error(f"Error type: {type(e).__name__}")
            
            # Check if it's a 404 error about unknown order item ID
            if "404" in error_msg or "Not Found" in error_msg:
                logger.error(f"⚠️ This usually means:")
                logger.error(f"   1. The orderItemId '{order_item_id}' doesn't exist, OR")
                logger.error(f"   2. The order item is not FBR (Fulfilled By Retailer)")
                logger.error(f"   3. Only FBR items can get shipping labels")
                logger.error(f"   Make sure you're using the orderItemId from orderItems, not the orderId")
            
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {}
    
    def create_shipping_label(self, order_item_id: str, 
                             shipping_label_offer_id: Optional[str] = None,
                             quantity: int = 1) -> Dict[str, Any]:
        """
        Create a shipping label for an order item
        
        Args:
            order_item_id: Order item ID
            shipping_label_offer_id: Optional shipping label offer ID
                If not provided, will fetch delivery options and use "verzenden via bol" offer
            quantity: Quantity for the order item (default: 1)
            
        Returns:
            Shipping label creation response with processStatus containing shipmentId
        """
        endpoint = "/shipping-labels"
        payload = {
            'orderItems': [
                {
                    'orderItemId': order_item_id,
                    'quantity': quantity
                }
            ]
        }
        
        # If no offer ID provided, try to find "verzenden via bol" offer
        if not shipping_label_offer_id:
            try:
                delivery_options_response = self.get_delivery_options(order_item_id, quantity)
                delivery_options = delivery_options_response.get('deliveryOptions', [])
                
                # Look for "verzenden via bol" offer
                for option in delivery_options:
                    label_display_name = option.get('labelDisplayName', '').lower()
                    transporter_code = option.get('transporterCode', '').lower()
                    if 'verzenden via bol' in label_display_name or 'bol' in label_display_name:
                        shipping_label_offer_id = option.get('shippingLabelOfferId')
                        logger.info(f"Found 'verzenden via bol' offer: {shipping_label_offer_id}")
                        break
                
                # If not found, use first available offer
                if not shipping_label_offer_id and delivery_options:
                    shipping_label_offer_id = delivery_options[0].get('shippingLabelOfferId')
                    logger.warning(f"'verzenden via bol' not found, using first available offer: {shipping_label_offer_id}")
                    
            except Exception as e:
                logger.warning(f"Could not fetch delivery options: {e}. Creating label without offer ID.")
        
        if shipping_label_offer_id:
            payload['shippingLabelOfferId'] = shipping_label_offer_id
        
        logger.info(f"🔍 Creating shipping label for order item {order_item_id}...")
        logger.info(f"📦 Payload: {payload}")
        try:
            response = self._make_request('POST', endpoint, json=payload)
            logger.info(f"✅ Create shipping label response keys: {list(response.keys())}")
            return response
        except Exception as e:
            logger.error(f"❌ Failed to create shipping label: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def get_process_status(self, process_status_id: str) -> Dict[str, Any]:
        """
        Get the status of an asynchronous process
        
        Args:
            process_status_id: Process status ID
            
        Returns:
            Process status including entityId (shippingLabelId) when SUCCESS
        """
        # Note: Process status uses /shared/ not /retailer/ path
        url = f"https://api.bol.com/shared/process-status/{process_status_id}"
        headers = self._get_headers()
        
        logger.info(f"Checking process status for {process_status_id}...")
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"API request failed: GET {url}")
            logger.error(f"Status: {e.response.status_code}")
            logger.error(f"Response: {e.response.text}")
            
            # If unauthorized, try refreshing token once
            if e.response.status_code == 401:
                logger.info("Received 401, refreshing token and retrying...")
                self.access_token = None  # Force token refresh
                headers = self._get_headers()
                response = self.session.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            
            raise Exception(f"API request failed: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            raise Exception(f"Request failed: {e}")
    
    def get_shipping_label_info(self, shipping_label_id: str) -> Dict[str, str]:
        """
        Get shipping label track & trace information using HEAD request (fast, recommended by Bol.com)
        
        This uses a HEAD request which is faster than GET since it only returns headers.
        Use this when you only need Track & Trace code and Transporter code without the label PDF/ZPL.
        
        Args:
            shipping_label_id: Shipping label ID (from process status entityId)
            
        Returns:
            Dictionary with:
            - 'track_and_trace': Track and trace code from X-Track-And-Trace-Code header
            - 'transporter_code': Transporter code from X-Transporter-Code header
        """
        endpoint = f"/shipping-labels/{shipping_label_id}"
        url = f"{self.API_BASE_URL}{endpoint}"
        
        # For shipping labels, use standard headers without format-specific accept
        token = self._get_access_token()
        headers = {
            'Authorization': f'{self.token_type} {token}',
            'Accept': 'application/vnd.retailer.v10+json, application/pdf, text/plain, */*'
        }
        
        logger.info(f"Fetching shipping label info (HEAD request) for shipping label ID {shipping_label_id}...")
        
        try:
            response = self.session.head(url, headers=headers)
            response.raise_for_status()
            
            # Extract headers
            track_and_trace = response.headers.get('X-Track-And-Trace-Code', '')
            transporter_code = response.headers.get('X-Transporter-Code', '')
            
            logger.info(f"✅ Track and Trace: {track_and_trace}, Transporter: {transporter_code}")
            
            return {
                'track_and_trace': track_and_trace,
                'transporter_code': transporter_code
            }
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"API request failed: HEAD {url}")
            logger.error(f"Status: {e.response.status_code}")
            logger.error(f"Response: {e.response.text}")
            
            # If unauthorized, try refreshing token once
            if e.response.status_code == 401:
                logger.info("Received 401, refreshing token and retrying...")
                self.access_token = None  # Force token refresh
                headers = self._get_headers()
                response = self.session.head(url, headers=headers)
                response.raise_for_status()
                
                track_and_trace = response.headers.get('X-Track-And-Trace-Code', '')
                transporter_code = response.headers.get('X-Transporter-Code', '')
                
                return {
                    'track_and_trace': track_and_trace,
                    'transporter_code': transporter_code
                }
            
            raise Exception(f"API request failed: {e}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            raise Exception(f"Request failed: {e}")
    
    def get_shipping_label(self, shipping_label_id: str, label_format: str = "ZPL") -> Dict[str, Any]:
        """
        Get shipping label data (including ZPL) using shipping label ID
        
        This endpoint can return:
        - Raw ZPL/PDF data in response body
        - Track and Trace code in X-Track-And-Trace-Code header
        - Transporter code in X-Transporter-Code header
        
        Args:
            shipping_label_id: Shipping label ID (from process status entityId)
            label_format: Label format ("ZPL" or "PDF", default: "ZPL")
            
        Returns:
            Dictionary with:
            - 'data': Label data (ZPL text or base64-encoded PDF)
            - 'track_and_trace': Track and trace code from header
            - 'transporter_code': Transporter code from header
            - 'content_type': Response content type
        """
        endpoint = f"/shipping-labels/{shipping_label_id}"
        url = f"{self.API_BASE_URL}{endpoint}"
        
        # For shipping labels, use appropriate Accept header based on format
        token = self._get_access_token()
        
        # ZPL format requires text/plain accept header
        if label_format == "ZPL":
            accept_header = 'text/plain'
        elif label_format == "PDF":
            accept_header = 'application/pdf'
        else:
            # Try to accept multiple formats
            accept_header = 'text/plain, application/pdf, application/vnd.retailer.v10+json'
        
        headers = {
            'Authorization': f'{self.token_type} {token}',
            'Accept': accept_header
        }
        
        # Add format parameter
        params = {}
        if label_format:
            params['format'] = label_format
        
        logger.info(f"Fetching shipping label (format: {label_format}) for shipping label ID {shipping_label_id}...")
        
        try:
            response = self.session.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            # Extract headers
            track_and_trace = response.headers.get('X-Track-And-Trace-Code', '')
            transporter_code = response.headers.get('X-Transporter-Code', '')
            content_type = response.headers.get('Content-Type', '')
            
            logger.info(f"✅ Response - Track & Trace: {track_and_trace}, Transporter: {transporter_code}, Content-Type: {content_type}")
            
            # Get the response content based on format
            if label_format == "ZPL" or 'text/plain' in content_type:
                # ZPL should be plain text
                try:
                    label_data = response.text
                    logger.info(f"✅ Received ZPL label as text ({len(label_data)} characters)")
                except Exception as e:
                    logger.warning(f"Could not decode as text: {e}, trying as bytes")
                    label_data = response.content
            elif label_format == "PDF" or 'pdf' in content_type:
                # PDF is binary
                label_data = response.content
                logger.info(f"✅ Received PDF label ({len(label_data)} bytes)")
            else:
                # Try JSON first, then fallback to raw content
                try:
                    json_response = response.json()
                    logger.info(f"✅ Received JSON response with keys: {list(json_response.keys())}")
                    
                    # Extract label data from JSON structure
                    label_data = None
                    if 'label' in json_response:
                        label_obj = json_response.get('label', {})
                        label_data = label_obj.get('data') or label_obj.get('labelData') or label_obj.get('zpl')
                    elif 'data' in json_response:
                        label_data = json_response.get('data')
                    elif 'labelData' in json_response:
                        label_data = json_response.get('labelData')
                    elif 'zpl' in json_response:
                        label_data = json_response.get('zpl')
                    
                    if not label_data:
                        logger.info(f"No specific label field found in JSON")
                        label_data = json_response
                except ValueError:
                    # Not JSON, use raw content
                    label_data = response.text if 'text' in content_type else response.content
                    logger.info(f"✅ Received raw content ({len(str(label_data))} chars/bytes)")
            
            return {
                'data': label_data,
                'track_and_trace': track_and_trace,
                'transporter_code': transporter_code,
                'content_type': content_type
            }
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"API request failed: GET {url}")
            logger.error(f"Status: {e.response.status_code}")
            logger.error(f"Response: {e.response.text}")
            
            # If unauthorized, try refreshing token once
            if e.response.status_code == 401:
                logger.info("Received 401, refreshing token and retrying...")
                self.access_token = None  # Force token refresh
                token = self._get_access_token()
                
                # Recreate headers with same accept header
                if label_format == "ZPL":
                    accept_header = 'text/plain'
                elif label_format == "PDF":
                    accept_header = 'application/pdf'
                else:
                    accept_header = 'text/plain, application/pdf, application/vnd.retailer.v10+json'
                
                headers = {
                    'Authorization': f'{self.token_type} {token}',
                    'Accept': accept_header
                }
                response = self.session.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                # Extract response data
                track_and_trace = response.headers.get('X-Track-And-Trace-Code', '')
                transporter_code = response.headers.get('X-Transporter-Code', '')
                content_type = response.headers.get('Content-Type', '')
                
                try:
                    json_response = response.json()
                    label_data = None
                    if 'label' in json_response:
                        label_obj = json_response.get('label', {})
                        label_data = label_obj.get('data') or label_obj.get('labelData') or label_obj.get('zpl')
                    elif 'data' in json_response:
                        label_data = json_response.get('data')
                    elif 'labelData' in json_response:
                        label_data = json_response.get('labelData')
                    elif 'zpl' in json_response:
                        label_data = json_response.get('zpl')
                    
                    if not label_data:
                        label_data = json_response
                except ValueError:
                    if label_format == "ZPL":
                        try:
                            label_data = response.text
                        except Exception:
                            label_data = response.content
                    else:
                        label_data = response.content
                
                return {
                    'data': label_data,
                    'track_and_trace': track_and_trace,
                    'transporter_code': transporter_code,
                    'content_type': content_type
                }
            
            raise Exception(f"API request failed: {e}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            raise Exception(f"Request failed: {e}")
    
    def get_shipment_shipping_label(self, shipment_id: str, label_format: str = "ZPL") -> Dict[str, Any]:
        """
        Get shipping label data (including ZPL) for a shipment (alternative endpoint)
        
        This endpoint can return:
        - Raw ZPL/PDF data in response body
        - Track and Trace code in X-Track-And-Trace-Code header
        - Transporter code in X-Transporter-Code header
        
        Args:
            shipment_id: Shipment ID
            label_format: Label format (default: "ZPL")
            
        Returns:
            Dictionary with:
            - 'data': Label data (ZPL text or base64-encoded PDF)
            - 'track_and_trace': Track and trace code from header
            - 'transporter_code': Transporter code from header
            - 'content_type': Response content type
        """
        endpoint = f"/shipments/{shipment_id}/shipping-label"
        params = {'format': label_format} if label_format else {}
        url = f"{self.API_BASE_URL}{endpoint}"
        headers = self._get_headers()
        
        logger.info(f"Fetching shipping label (format: {label_format}) for shipment {shipment_id}...")
        
        try:
            response = self.session.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            # Extract headers
            track_and_trace = response.headers.get('X-Track-And-Trace-Code', '')
            transporter_code = response.headers.get('X-Transporter-Code', '')
            content_type = response.headers.get('Content-Type', '')
            
            logger.info(f"Response headers - Track and Trace: {track_and_trace}, Transporter: {transporter_code}, Content-Type: {content_type}")
            
            # Try to parse as JSON first (some APIs return JSON)
            label_data = None
            try:
                json_response = response.json()
                # If it's JSON, extract label data from common structures
                if 'label' in json_response:
                    label_obj = json_response.get('label', {})
                    label_data = label_obj.get('data') or label_obj.get('labelData')
                elif 'data' in json_response:
                    label_data = json_response.get('data')
                elif 'labelData' in json_response:
                    label_data = json_response.get('labelData')
                else:
                    # Return full JSON response
                    return {
                        'data': json_response,
                        'track_and_trace': track_and_trace,
                        'transporter_code': transporter_code,
                        'content_type': content_type
                    }
            except ValueError:
                # Not JSON, treat as raw binary/text data
                label_data = response.content
            
            # Convert binary data to base64 string if needed
            if isinstance(label_data, bytes):
                import base64
                # For ZPL, try to decode as UTF-8 first
                try:
                    label_data = label_data.decode('utf-8')
                    logger.info(f"Decoded label as UTF-8 text ({len(label_data)} chars)")
                except UnicodeDecodeError:
                    # If not UTF-8, encode as base64
                    label_data = base64.b64encode(label_data).decode('utf-8')
                    logger.info(f"Encoded label as base64 ({len(label_data)} chars)")
            
            return {
                'data': label_data,
                'track_and_trace': track_and_trace,
                'transporter_code': transporter_code,
                'content_type': content_type
            }
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"API request failed: GET {url}")
            logger.error(f"Status: {e.response.status_code}")
            logger.error(f"Response: {e.response.text}")
            
            # If unauthorized, try refreshing token once
            if e.response.status_code == 401:
                logger.info("Received 401, refreshing token and retrying...")
                self.access_token = None  # Force token refresh
                headers = self._get_headers()
                response = self.session.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                # Repeat extraction logic
                track_and_trace = response.headers.get('X-Track-And-Trace-Code', '')
                transporter_code = response.headers.get('X-Transporter-Code', '')
                content_type = response.headers.get('Content-Type', '')
                
                label_data = None
                try:
                    json_response = response.json()
                    if 'label' in json_response:
                        label_obj = json_response.get('label', {})
                        label_data = label_obj.get('data') or label_obj.get('labelData')
                    elif 'data' in json_response:
                        label_data = json_response.get('data')
                    elif 'labelData' in json_response:
                        label_data = json_response.get('labelData')
                    else:
                        return {
                            'data': json_response,
                            'track_and_trace': track_and_trace,
                            'transporter_code': transporter_code,
                            'content_type': content_type
                        }
                except ValueError:
                    label_data = response.content
                
                if isinstance(label_data, bytes):
                    import base64
                    try:
                        label_data = label_data.decode('utf-8')
                    except UnicodeDecodeError:
                        label_data = base64.b64encode(label_data).decode('utf-8')
                
                return {
                    'data': label_data,
                    'track_and_trace': track_and_trace,
                    'transporter_code': transporter_code,
                    'content_type': content_type
                }
            
            raise Exception(f"API request failed: {e}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            raise Exception(f"Request failed: {e}")
    
    def update_shipment(self, shipment_id: str, 
                       transporter_code: Optional[str] = None,
                       track_and_trace: Optional[str] = None) -> Dict[str, Any]:
        """
        Update shipment information (mark as shipped)
        
        Args:
            shipment_id: Shipment ID
            transporter_code: Optional transporter code
            track_and_trace: Optional track and trace number
            
        Returns:
            Updated shipment data
        """
        endpoint = f"/shipments/{shipment_id}"
        payload = {}
        
        if transporter_code:
            payload['transporterCode'] = transporter_code
        if track_and_trace:
            payload['trackAndTrace'] = track_and_trace
        
        logger.info(f"Updating shipment {shipment_id}...")
        return self._make_request('PUT', endpoint, json=payload)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.session.close()

