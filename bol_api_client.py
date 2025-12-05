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
    
    def get_shipping_label_offers(self, order_item_id: str) -> Dict[str, Any]:
        """
        Get available shipping label offers for an order item
        
        Args:
            order_item_id: Order item ID
            
        Returns:
            Dictionary containing available shipping label offers
        """
        # Note: This endpoint may not be available in all API versions
        # If it fails, we'll create label without offer ID
        endpoint = f"/shipping-labels/{order_item_id}"
        logger.info(f"Fetching shipping label offers for order item {order_item_id}...")
        try:
            # Try with different Accept header for shipping labels endpoint
            token = self._get_access_token()
            headers = {
                'Authorization': f'{self.token_type} {token}',
                'Accept': 'application/json',  # Different Accept header for this endpoint
            }
            url = f"{self.API_BASE_URL}{endpoint}"
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # If endpoint doesn't exist or fails, return empty dict
            logger.debug(f"Could not fetch shipping label offers (endpoint may not be available): {e}")
            return {}
    
    def create_shipping_label(self, order_item_id: str, 
                             shipping_label_offer_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a shipping label for an order item
        
        Args:
            order_item_id: Order item ID
            shipping_label_offer_id: Optional shipping label offer ID
                If not provided, will use "verzenden via bol" offer
            
        Returns:
            Shipping label data including ZPL format
        """
        endpoint = "/shipments"
        payload = {
            'orderItems': [{'orderItemId': order_item_id}]
        }
        
        # If no offer ID provided, try to find "verzenden via bol" offer
        if not shipping_label_offer_id:
            try:
                offers_response = self.get_shipping_label_offers(order_item_id)
                offers = offers_response.get('offers', [])
                
                # Look for "verzenden via bol" offer
                for offer in offers:
                    if 'verzenden via bol' in offer.get('label', {}).get('transporter', {}).get('name', '').lower():
                        shipping_label_offer_id = offer.get('id')
                        logger.info(f"Found 'verzenden via bol' offer: {shipping_label_offer_id}")
                        break
                
                # If not found, use first available offer
                if not shipping_label_offer_id and offers:
                    shipping_label_offer_id = offers[0].get('id')
                    logger.warning(f"'verzenden via bol' not found, using first available offer: {shipping_label_offer_id}")
                    
            except Exception as e:
                logger.warning(f"Could not fetch shipping label offers: {e}. Creating label without offer ID.")
        
        if shipping_label_offer_id:
            payload['shippingLabelOfferId'] = shipping_label_offer_id
        
        logger.info(f"Creating shipping label for order item {order_item_id}...")
        return self._make_request('POST', endpoint, json=payload)
    
    def get_shipping_label(self, shipment_id: str, label_format: str = "ZPL") -> Dict[str, Any]:
        """
        Get shipping label data (including ZPL) for a shipment
        
        Args:
            shipment_id: Shipment ID
            label_format: Label format (default: "ZPL")
            
        Returns:
            Shipping label data including ZPL format
        """
        endpoint = f"/shipments/{shipment_id}/shipping-label"
        params = {'format': label_format} if label_format else {}
        logger.info(f"Fetching shipping label (format: {label_format}) for shipment {shipment_id}...")
        return self._make_request('GET', endpoint, params=params)
    
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

