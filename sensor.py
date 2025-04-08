from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN

SENSOR_TYPES = {
    "voltage": {
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "V"
    },
    "current": {
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "A"
    },
    "frequency": {
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "Hz"
    },
    "active_power": {
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "W"
    },
    "full_power": {
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": "W"
    },
    "active_energy": {
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": "Wh"
    },
    "full_energy": {
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": "Wh"
    }
}

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device = data["device"]

    entities = []
    for sensor_key, props in SENSOR_TYPES.items():
        entities.append(NovatekSensor(coordinator, sensor_key, entry.title, device))
    async_add_entities(entities)

class NovatekSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, sensor_type: str, device_name: str, device):
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._device_name = device_name
        self._device = device
        props = SENSOR_TYPES[sensor_type]
        self._attr_device_class = props["device_class"]
        self._attr_state_class = props["state_class"]
        self._attr_native_unit_of_measurement = props["unit"]
        self._attr_unique_id = f"{DOMAIN}_{device_name}_{sensor_type}"
        if sensor_type.endswith("energy"):
            name_prefix = "Active" if sensor_type == "active_energy" else "Full"
            self._attr_name = f"{device_name} {name_prefix} energy"
        elif sensor_type.endswith("power"):
            name_prefix = "Active" if sensor_type == "active_power" else "Full"
            self._attr_name = f"{device_name} {name_prefix} power"
        else:
            self._attr_name = f"{device_name} {sensor_type}"

    @property
    def native_value(self):
        return self.coordinator.data.get(self._sensor_type)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device._host)},
            "name": self._device_name,
            "manufacturer": "Novatek-Electro",
            "model": self._device.model or "Novatek Device"
        }
