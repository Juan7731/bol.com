"""
Data Transfer Objects (DTOs) for Bol.com API responses
Provides clean, typed objects instead of raw dictionaries
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class OrderItem:
    """Represents a single item in an order"""
    order_item_id: str
    ean: Optional[str] = None
    quantity: int = 1
    quantity_shipped: int = 0
    quantity_cancelled: int = 0
    unit_price: Optional[float] = None
    fulfilment_method: Optional[str] = None
    offer_reference: Optional[str] = None
    product_title: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderItem':
        """Create OrderItem from API response dictionary"""
        # fulfilmentMethod is directly on the order item (not nested)
        fulfilment_method = data.get('fulfilmentMethod')
        # Also try nested structure for backwards compatibility
        if not fulfilment_method:
            fulfilment_method = data.get('fulfilment', {}).get('method')
        
        return cls(
            order_item_id=data.get('orderItemId', ''),
            ean=data.get('ean'),
            quantity=data.get('quantity', 1),
            quantity_shipped=data.get('quantityShipped', 0),
            quantity_cancelled=data.get('quantityCancelled', 0),
            unit_price=data.get('unitPrice'),
            fulfilment_method=fulfilment_method,
            offer_reference=data.get('offerReference'),
            product_title=data.get('product', {}).get('title')
        )


@dataclass
class CustomerDetails:
    """Customer information for an order"""
    first_name: Optional[str] = None
    surname: Optional[str] = None
    street_name: Optional[str] = None
    house_number: Optional[str] = None
    house_number_extension: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    country_code: Optional[str] = None
    email: Optional[str] = None
    delivery_phone_number: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Get full customer name"""
        parts = [self.first_name or '', self.surname or '']
        return ' '.join(filter(None, parts)).strip()
    
    @property
    def full_address(self) -> str:
        """Get full address as string"""
        parts = [
            self.street_name or '',
            self.house_number or '',
            self.house_number_extension or ''
        ]
        street = ' '.join(filter(None, parts)).strip()
        
        parts = [self.zip_code or '', self.city or '']
        city = ' '.join(filter(None, parts)).strip()
        
        return f"{street}, {city}".strip(', ')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomerDetails':
        """Create CustomerDetails from API response dictionary"""
        customer = data.get('customerDetails', {})
        billing = customer.get('billingDetails', {})
        ship_to = customer.get('shipmentDetails', {})
        
        return cls(
            first_name=ship_to.get('firstName') or billing.get('firstName'),
            surname=ship_to.get('surname') or billing.get('surname'),
            street_name=ship_to.get('streetName') or billing.get('streetName'),
            house_number=ship_to.get('houseNumber') or billing.get('houseNumber'),
            house_number_extension=ship_to.get('houseNumberExtension') or billing.get('houseNumberExtension'),
            zip_code=ship_to.get('zipCode') or billing.get('zipCode'),
            city=ship_to.get('city') or billing.get('city'),
            country_code=ship_to.get('countryCode') or billing.get('countryCode'),
            email=billing.get('email'),
            delivery_phone_number=ship_to.get('deliveryPhoneNumber')
        )


@dataclass
class Order:
    """Represents a Bol.com order"""
    order_id: str
    order_placed_date_time: Optional[datetime] = None
    order_items: List[OrderItem] = field(default_factory=list)
    customer_details: Optional[CustomerDetails] = None
    status: str = "OPEN"
    shipment_details: Optional[Dict[str, Any]] = None
    
    @property
    def total_items(self) -> int:
        """Get total number of items in order"""
        return sum(item.quantity for item in self.order_items)
    
    @property
    def unique_eans(self) -> List[str]:
        """Get list of unique EANs in order"""
        eans = [item.ean for item in self.order_items if item.ean]
        return list(set(eans))
    
    @property
    def is_single(self) -> bool:
        """Check if order is Single type (one item, one EAN, quantity 1)"""
        return (len(self.order_items) == 1 and 
                self.order_items[0].quantity == 1 and
                len(self.unique_eans) == 1)
    
    @property
    def is_singleline(self) -> bool:
        """Check if order is SingleLine type (multiple units of same EAN)"""
        return (len(self.order_items) == 1 and 
                self.order_items[0].quantity > 1 and
                len(self.unique_eans) == 1)
    
    @property
    def is_multi(self) -> bool:
        """Check if order is Multi type (different items/multiple EANs)"""
        return len(self.unique_eans) > 1
    
    @property
    def category(self) -> str:
        """Get order category: Single, SingleLine, or Multi"""
        if self.is_single:
            return "Single"
        elif self.is_singleline:
            return "SingleLine"
        elif self.is_multi:
            return "Multi"
        else:
            return "Unknown"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """Create Order from API response dictionary"""
        # Parse order items
        order_items = [
            OrderItem.from_dict(item_data)
            for item_data in data.get('orderItems', [])
        ]
        
        # Parse customer details
        customer_details = CustomerDetails.from_dict(data)
        
        # Parse date
        date_str = data.get('orderPlacedDateTime')
        order_date = None
        if date_str:
            try:
                # Bol.com uses ISO 8601 format
                order_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        
        return cls(
            order_id=data.get('orderId', ''),
            order_placed_date_time=order_date,
            order_items=order_items,
            customer_details=customer_details,
            status=data.get('status', 'OPEN'),
            shipment_details=data.get('shipmentDetails')
        )


@dataclass
class ShippingLabel:
    """Represents a shipping label"""
    shipment_id: Optional[str] = None
    label_type: Optional[str] = None
    label_format: Optional[str] = None  # e.g., "ZPL"
    label_data: Optional[str] = None  # Base64 encoded or raw ZPL
    track_and_trace: Optional[str] = None
    transporter_code: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShippingLabel':
        """Create ShippingLabel from API response dictionary"""
        return cls(
            shipment_id=data.get('shipmentId'),
            label_type=data.get('labelType'),
            label_format=data.get('labelFormat'),
            label_data=data.get('labelData'),
            track_and_trace=data.get('trackAndTrace'),
            transporter_code=data.get('transporterCode')
        )


@dataclass
class Shipment:
    """Represents a shipment"""
    shipment_id: str
    order_id: Optional[str] = None
    shipment_date_time: Optional[datetime] = None
    shipment_reference: Optional[str] = None
    transport: Optional[Dict[str, Any]] = None
    order_items: List[OrderItem] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Shipment':
        """Create Shipment from API response dictionary"""
        # Parse order items
        order_items = [
            OrderItem.from_dict(item_data)
            for item_data in data.get('orderItems', [])
        ]
        
        # Parse date
        date_str = data.get('shipmentDateTime')
        shipment_date = None
        if date_str:
            try:
                shipment_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        
        return cls(
            shipment_id=data.get('shipmentId', ''),
            order_id=data.get('orderId'),
            shipment_date_time=shipment_date,
            shipment_reference=data.get('shipmentReference'),
            transport=data.get('transport'),
            order_items=order_items
        )

