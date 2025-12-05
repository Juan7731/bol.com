# Bol.com Retailer API v10 - Python Client

A production-ready Python client for the Bol.com Retailer API v10, providing OAuth 2.0 authentication and clean DTOs for order processing.

## Features

- ✅ OAuth 2.0 authentication with automatic token refresh
- ✅ Retrieve all open orders with automatic pagination
- ✅ Clean Data Transfer Objects (DTOs) instead of raw JSON
- ✅ Order classification (Single, SingleLine, Multi)
- ✅ Excel file generation with correct format
- ✅ Automatic SFTP upload
- ✅ Email notifications with daily summaries
- ✅ Duplicate order prevention via database
- ✅ Status callback handler (HTML file processing)
- ✅ Multi-account support (Trivium, Jean)
- ✅ Configuration management (Python functions)
- ✅ Comprehensive error handling and logging
- ✅ Production-ready code structure

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Setup

1. **Clone or download this repository**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your credentials:**
   
   Edit `test_bol_api.py` or create a configuration file with your Bol.com credentials:
   - Client ID
   - Client Secret

## Quick Start

### Basic Usage

```python
from bol_api_client import BolAPIClient
from bol_dtos import Order

# Initialize client
client = BolAPIClient(
    client_id="your-client-id",
    client_secret="your-client-secret",
    test_mode=True  # Use test environment
)

# Get all open orders
orders_data = client.get_all_open_orders()

# Parse into DTOs
orders = [Order.from_dict(order_data) for order_data in orders_data]

# Access order properties
for order in orders:
    print(f"Order ID: {order.order_id}")
    print(f"Category: {order.category}")  # Single, SingleLine, or Multi
    print(f"Customer: {order.customer_details.full_name}")
    print(f"Total Items: {order.total_items}")
```

### Run Test Script

The included test script demonstrates all functionality:

```bash
python test_bol_api.py
```

This will:
1. Test OAuth 2.0 authentication
2. Retrieve open orders
3. Parse orders into DTOs
4. Classify orders by type
5. Display results

## API Client Methods

### Authentication

Authentication is handled automatically. The client will:
- Request a new token when needed
- Refresh tokens before expiration (5-minute buffer)
- Retry requests on 401 errors

### Order Operations

#### Get Orders (Paginated)

```python
response = client.get_orders(status="OPEN", page=1, limit=100)
# Returns: Dictionary with 'orders' and 'pagination' keys
```

#### Get All Open Orders

```python
orders_data = client.get_all_open_orders()
# Returns: List of all open orders (handles pagination automatically)
```

#### Get Single Order

```python
order_data = client.get_order(order_id="1234567890")
# Returns: Single order dictionary
```

### Shipment Operations

#### Get Shipments

```python
shipments = client.get_shipments(order_id="1234567890", page=1, limit=100)
```

#### Get Single Shipment

```python
shipment = client.get_shipment(shipment_id="shipment-123")
```

#### Create Shipping Label

```python
label = client.create_shipping_label(
    order_item_id="item-123",
    shipping_label_offer_id="offer-456"  # Optional
)
# Returns shipping label with ZPL format data
```

#### Update Shipment (Mark as Shipped)

```python
client.update_shipment(
    shipment_id="shipment-123",
    transporter_code="POSTNL",
    track_and_trace="3SABC1234567890"
)
```

## Data Transfer Objects (DTOs)

All API responses are parsed into clean, typed objects:

### Order

```python
order = Order.from_dict(api_response)

# Properties
order.order_id                    # str
order.status                      # str (OPEN, SHIPPED, etc.)
order.order_placed_date_time      # datetime
order.order_items                 # List[OrderItem]
order.customer_details            # CustomerDetails
order.total_items                 # int
order.unique_eans                 # List[str]
order.category                    # str: "Single", "SingleLine", or "Multi"
order.is_single                   # bool
order.is_singleline               # bool
order.is_multi                    # bool
```

### OrderItem

```python
item = order.order_items[0]

# Properties
item.order_item_id                # str
item.ean                          # str
item.quantity                     # int
item.quantity_shipped             # int
item.quantity_cancelled           # int
item.unit_price                   # float
item.product_title                # str
```

### CustomerDetails

```python
customer = order.customer_details

# Properties
customer.full_name                # str (computed)
customer.full_address             # str (computed)
customer.first_name               # str
customer.surname                  # str
customer.email                    # str
customer.zip_code                 # str
customer.city                     # str
```

## Order Classification

Orders are automatically classified into three categories:

- **Single**: One item, one EAN, quantity = 1
- **SingleLine**: Multiple units of the same EAN
- **Multi**: Different items / multiple EANs

```python
order = Order.from_dict(order_data)

if order.is_single:
    # Handle single item order
elif order.is_singleline:
    # Handle single line order
elif order.is_multi:
    # Handle multi-item order
```

## Error Handling

The client includes comprehensive error handling:

- **Authentication errors**: Automatically retries with token refresh
- **HTTP errors**: Logs detailed error information
- **Network errors**: Provides clear error messages

Example:

```python
try:
    orders = client.get_all_open_orders()
except Exception as e:
    print(f"Error: {e}")
    # Handle error appropriately
```

## Logging

The client uses Python's logging module. Configure logging level:

```python
import logging

logging.basicConfig(level=logging.DEBUG)  # For detailed logs
# or
logging.basicConfig(level=logging.INFO)   # For normal operation
```

## Token Refresh Logic

The client automatically manages OAuth tokens:

1. **Token Request**: On first API call or when token expires
2. **Token Storage**: Access token and expiration time stored in memory
3. **Automatic Refresh**: Token refreshed 5 minutes before expiration
4. **Retry Logic**: On 401 errors, token is refreshed and request retried

You don't need to manually handle token refresh - it's all automatic!

## Test vs Production Environment

The client supports both test and production environments:

```python
# Test environment (default)
client = BolAPIClient(client_id, client_secret, test_mode=True)

# Production environment
client = BolAPIClient(client_id, client_secret, test_mode=False)
```

**Note**: Currently, both environments use the same endpoints. The `test_mode` parameter is included for future use when Bol.com provides separate test endpoints.

## Example: Complete Workflow

```python
from bol_api_client import BolAPIClient
from bol_dtos import Order

# Initialize
client = BolAPIClient(
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# Get all open orders
orders_data = client.get_all_open_orders()

# Parse and process
orders = [Order.from_dict(data) for data in orders_data]

# Classify and group
single_orders = [o for o in orders if o.is_single]
singleline_orders = [o for o in orders if o.is_singleline]
multi_orders = [o for o in orders if o.is_multi]

# Process each category
for order in single_orders:
    print(f"Processing single order: {order.order_id}")
    # Your processing logic here

# Create shipping labels
for order in orders:
    for item in order.order_items:
        label = client.create_shipping_label(item.order_item_id)
        # Use label.label_data (ZPL format) for printing
```

## API Documentation

For complete API documentation, refer to:
- [Bol.com Retailer API v10 - Orders & Shipments](https://api.bol.com/retailer/public/Retailer-API/v10/functional/retailer-api/orders-shipments.html)
- [Bol.com Retailer API v10 - Shipping Labels](https://api.bol.com/retailer/public/Retailer-API/v10/functional/retailer-api/shipping-labels.html)

## Project Structure

```
.
├── bol_api_client.py      # Main API client class
├── bol_dtos.py            # Data Transfer Objects
├── test_bol_api.py        # Test script
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Milestone 1 Status

✅ **Completed:**
- OAuth 2.0 authentication with automatic token refresh
- Retrieve all open orders with pagination
- Parse JSON responses into clean DTOs
- Order classification logic
- Comprehensive test script
- Production-ready error handling

## Next Steps (Future Milestones)

- Generate shipping labels in ZPL format
- Excel file generation with specific format
- FTP upload functionality
- Email notifications
- Admin interface (HTML/PHP)
- Status callback handling from FTP

## Support

For issues or questions:
1. Check the API documentation links above
2. Review error logs for detailed error messages
3. Ensure credentials are correct and have proper permissions

## License

This code is provided as-is for the Bol.com order processing project.

