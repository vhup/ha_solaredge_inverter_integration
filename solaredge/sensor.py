"""Support for SolarEdge Monitoring API."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .solaredge import Solaredge

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower, UnitOfElectricPotential
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import CONF_SITE_ID, CONF_INVERTER_ID, DATA_API_CLIENT, DOMAIN
from .coordinator import (
    SolarEdgeDataService,
    SolarEdgeInverterDetailsDataService,
)


@dataclass(frozen=True)
class SolarEdgeSensorEntityRequiredKeyMixin:
    """Sensor entity description with json_key for SolarEdge."""
    json_key: str


@dataclass(frozen=True)
class SolarEdgeSensorEntityDescription(
    SensorEntityDescription, SolarEdgeSensorEntityRequiredKeyMixin
):
    """Sensor entity description for SolarEdge."""


SENSOR_TYPES = [
    SolarEdgeSensorEntityDescription(
        key="powerLimit",
        json_key="powerLimit",
        translation_key="powerLimit",
        icon="mdi:car-speed-limiter",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.POWER_FACTOR,
    ),
    SolarEdgeSensorEntityDescription(
        key="inverterMode",
        json_key="inverterMode",
        icon="mdi:cog-outline",
        translation_key="inverterMode",
        entity_registry_enabled_default=False,
    ),
    SolarEdgeSensorEntityDescription(
        key="totalEnergy",
        json_key="totalEnergy",
        translation_key="totalEnergy",
        icon="mdi:solar-power",
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SolarEdgeSensorEntityDescription(
        key="totalActivePower",
        json_key="totalActivePower",
        translation_key="totalActivePower",
        icon="mdi:solar-power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
    ),
    SolarEdgeSensorEntityDescription(
        key="L1Data_acVoltage",
        json_key="L1Data_acVoltage",
        translation_key="L1Data_acVoltage",
        icon="mdi:sine-wave",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
    )
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add an solarEdge entry."""
    # Add the needed sensors to hass
    api: Solaredge = hass.data[DOMAIN][entry.entry_id][DATA_API_CLIENT]

    sensor_factory = SolarEdgeSensorFactory(hass, entry.data[CONF_SITE_ID], entry.data[CONF_INVERTER_ID], api)
    for service in sensor_factory.all_services:
        service.async_setup()
        await service.coordinator.async_refresh()

    entities = []
    for sensor_type in SENSOR_TYPES:
        sensor = sensor_factory.create_sensor(sensor_type)
        if sensor is not None:
            entities.append(sensor)
    async_add_entities(entities)


class SolarEdgeSensorFactory:
    """Factory which creates sensors based on the sensor_key."""

    def __init__(self, hass: HomeAssistant, site_id: str, inverter_id: str, api: Solaredge) -> None:
        """Initialize the factory."""
        inverter = SolarEdgeInverterDetailsDataService(hass, api, site_id, inverter_id)
        self.all_services = [inverter]

        self.services: dict[
            str,
            tuple[
                type[SolarEdgeSensorEntity],
                SolarEdgeDataService,
            ],
        ] = {}

        for key in ("L1Data_acVoltage", "totalActivePower", "powerLimit", "totalEnergy", "inverterMode"):
            self.services[key] = (SolarEdgeInverterDetailsSensor, inverter)


    def create_sensor(
        self, sensor_type: SolarEdgeSensorEntityDescription
    ) -> SolarEdgeSensorEntity:
        """Create and return a sensor based on the sensor_key."""
        sensor_class, service = self.services[sensor_type.key]
        return sensor_class(sensor_type, service)


class SolarEdgeSensorEntity(
    CoordinatorEntity[DataUpdateCoordinator[None]], SensorEntity
):
    """Abstract class for a solaredge sensor."""

    _attr_has_entity_name = True

    entity_description: SolarEdgeSensorEntityDescription

    def __init__(
        self,
        description: SolarEdgeSensorEntityDescription,
        data_service: SolarEdgeDataService,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(data_service.coordinator)
        self.entity_description = description
        self.data_service = data_service
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data_service.site_id, data_service.inverter_id)}, manufacturer="SolarEdge"
        )

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        if not self.data_service.site_id:
            return None
        if not self.data_service.inverter_id:
            return None
        return f"{self.data_service.site_id}_{self.data_service.inverter_id}_{self.entity_description.key}"


class SolarEdgeInverterDetailsSensor(SolarEdgeSensorEntity):
    """Representation of an SolarEdge Monitoring API Inverter details."""

    def __init__(
        self,
        sensor_type: SolarEdgeSensorEntityDescription,
        data_service: SolarEdgeEnergyDetailsService,
    ) -> None:
        """Initialize the power flow sensor."""
        super().__init__(sensor_type, data_service)

        #self._attr_native_unit_of_measurement = data_service.unit

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        return self.data_service.attributes.get(self.entity_description.json_key)

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        return self.data_service.data.get(self.entity_description.json_key)

