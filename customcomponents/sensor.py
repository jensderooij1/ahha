"""
Albert Heijn API Sensor voor Home Assistant
Haalt uitgaven en kortingen op via de AH mobile app API
"""
import logging
import requests
import json
from datetime import datetime, timedelta
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

DOMAIN = "albert_heijn"
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=30)

# API Endpoints
AH_BASE_URL = "https://ms.ah.nl:8080/mobile-services"
AH_RECEIPT_URL = f"{AH_BASE_URL}/receipts/v1"
AH_PROFILE_URL = f"{AH_BASE_URL}/profile/v1"

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Albert Heijn sensor platform."""
    access_token = config.get(CONF_ACCESS_TOKEN)
    
    if not access_token:
        _LOGGER.error("Access token not provided")
        return
    
    # Create sensors
    sensors = [
        AlbertHeijnTotalSpentSensor(access_token),
        AlbertHeijnTotalDiscountSensor(access_token),
        AlbertHeijnReceiptCountSensor(access_token),
        AlbertHeijnLastReceiptSensor(access_token)
    ]
    
    add_entities(sensors, True)

class AlbertHeijnAPI:
    """Class to interact with Albert Heijn API."""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "AH/5.2.1 (Android 10)",
            "Content-Type": "application/json"
        }
    
    def get_receipts(self, limit: int = 50):
        """Get receipts from AH API."""
        try:
            url = f"{AH_RECEIPT_URL}/receipts"
            params = {
                "size": limit,
                "page": 0
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except requests.RequestException as e:
            _LOGGER.error(f"Error fetching receipts: {e}")
            return None
    
    def get_receipt_details(self, receipt_id: str):
        """Get detailed receipt information."""
        try:
            url = f"{AH_RECEIPT_URL}/receipts/{receipt_id}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except requests.RequestException as e:
            _LOGGER.error(f"Error fetching receipt details for {receipt_id}: {e}")
            return None

class AlbertHeijnBaseSensor(SensorEntity):
    """Base class for Albert Heijn sensors."""
    
    def __init__(self, access_token: str):
        """Initialize the sensor."""
        self.api = AlbertHeijnAPI(access_token)
        self._receipts_data = None
        self._last_update = None
    
    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update sensor data."""
        self._receipts_data = self.api.get_receipts()
        self._last_update = datetime.now()

class AlbertHeijnTotalSpentSensor(AlbertHeijnBaseSensor):
    """Sensor for total amount spent at Albert Heijn."""
    
    def __init__(self, access_token: str):
        super().__init__(access_token)
        self._attr_name = "AH Totaal Uitgegeven"
        self._attr_unique_id = "ah_total_spent"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:currency-eur"
    
    @property
    def native_value(self):
        """Return the total amount spent."""
        if not self._receipts_data or 'receipts' not in self._receipts_data:
            return 0
        
        total = 0
        for receipt in self._receipts_data['receipts']:
            if 'grandTotal' in receipt:
                # grandTotal is usually in cents, convert to euros
                total += receipt['grandTotal'] / 100
        
        return round(total, 2)
    
    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        if not self._receipts_data:
            return {}
        
        return {
            "receipt_count": len(self._receipts_data.get('receipts', [])),
            "last_update": self._last_update.isoformat() if self._last_update else None
        }

class AlbertHeijnTotalDiscountSensor(AlbertHeijnBaseSensor):
    """Sensor for total discount received at Albert Heijn."""
    
    def __init__(self, access_token: str):
        super().__init__(access_token)
        self._attr_name = "AH Totale Korting"
        self._attr_unique_id = "ah_total_discount"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:percent"
    
    @property
    def native_value(self):
        """Return the total discount received."""
        if not self._receipts_data or 'receipts' not in self._receipts_data:
            return 0
        
        total_discount = 0
        for receipt in self._receipts_data['receipts']:
            # Look for discount in different fields
            if 'discountTotal' in receipt:
                total_discount += receipt['discountTotal'] / 100
            elif 'bonusTotal' in receipt:
                total_discount += receipt['bonusTotal'] / 100
            
            # Also check individual items for discounts
            if 'receiptLines' in receipt:
                for line in receipt['receiptLines']:
                    if 'discount' in line:
                        total_discount += line['discount'] / 100
        
        return round(total_discount, 2)
    
    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        if not self._receipts_data:
            return {}
        
        total_spent = 0
        for receipt in self._receipts_data['receipts']:
            if 'grandTotal' in receipt:
                total_spent += receipt['grandTotal'] / 100
        
        discount_percentage = 0
        if total_spent > 0:
            discount_percentage = round((self.native_value / total_spent) * 100, 1)
        
        return {
            "discount_percentage": f"{discount_percentage}%",
            "total_spent": round(total_spent, 2),
            "last_update": self._last_update.isoformat() if self._last_update else None
        }

class AlbertHeijnReceiptCountSensor(AlbertHeijnBaseSensor):
    """Sensor for number of receipts."""
    
    def __init__(self, access_token: str):
        super().__init__(access_token)
        self._attr_name = "AH Aantal Bonnetjes"
        self._attr_unique_id = "ah_receipt_count"
        self._attr_icon = "mdi:receipt"
    
    @property
    def native_value(self):
        """Return the number of receipts."""
        if not self._receipts_data or 'receipts' not in self._receipts_data:
            return 0
        
        return len(self._receipts_data['receipts'])

class AlbertHeijnLastReceiptSensor(AlbertHeijnBaseSensor):
    """Sensor for last receipt information."""
    
    def __init__(self, access_token: str):
        super().__init__(access_token)
        self._attr_name = "AH Laatste Bonnetje"
        self._attr_unique_id = "ah_last_receipt"
        self._attr_icon = "mdi:receipt-text"
    
    @property
    def native_value(self):
        """Return the date of the last receipt."""
        if not self._receipts_data or 'receipts' not in self._receipts_data or not self._receipts_data['receipts']:
            return None
        
        last_receipt = self._receipts_data['receipts'][0]  # Assuming receipts are sorted by date
        if 'transactionDate' in last_receipt:
            return last_receipt['transactionDate']
        
        return None
    
    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        if not self._receipts_data or 'receipts' not in self._receipts_data or not self._receipts_data['receipts']:
            return {}
        
        last_receipt = self._receipts_data['receipts'][0]
        
        return {
            "store_name": last_receipt.get('storeName', 'Onbekend'),
            "store_address": last_receipt.get('storeAddress', 'Onbekend'),
            "total_amount": round(last_receipt.get('grandTotal', 0) / 100, 2),
            "receipt_number": last_receipt.get('receiptNumber', 'Onbekend'),
            "last_update": self._last_update.isoformat() if self._last_update else None
        }