"""Provides the data update coordinators for SolarEdge."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from typing import Any

from .solaredge import Solaredge
from stringcase import snakecase

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    LOGGER,
    INVERTER_UPDATE_DELAY
)


class SolarEdgeDataService(ABC):
    """Get and update the latest data."""

    coordinator: DataUpdateCoordinator[None]

    def __init__(self, hass: HomeAssistant, api: Solaredge, site_id: str, inverter_id: str ) -> None:
        """Initialize the data object."""
        self.api = api
        self.site_id = site_id
        self.inverter_id = inverter_id
        self.data: dict[str, Any] = {}
        self.attributes: dict[str, Any] = {}
        self.hass = hass

    @callback
    def async_setup(self) -> None:
        """Coordinator creation."""
        self.coordinator = DataUpdateCoordinator(
            self.hass,
            LOGGER,
            name=str(self),
            update_method=self.async_update_data,
            update_interval=self.update_interval,
        )

    @property
    @abstractmethod
    def update_interval(self) -> timedelta:
        """Update interval."""

    @abstractmethod
    def update(self) -> None:
        """Update data in executor."""

    async def async_update_data(self) -> None:
        """Update data."""
        await self.hass.async_add_executor_job(self.update)



class SolarEdgeInverterDetailsDataService(SolarEdgeDataService):
    """Get and update the latest inventory data."""

    @property
    def update_interval(self) -> timedelta:
        """Update interval."""
        return INVERTER_UPDATE_DELAY

    def update(self) -> None:
        """Update the data from the SolarEdge Monitoring API."""
        try:
            now = datetime.now()
            today = date.today()
            #midnight = datetime.combine(today, datetime.min.time())
            #data = self.api.get_inverterDetails(self.site_id, self.inverter_id,midnight.strftime("%Y-%m-%d %H:%M:%S"),now.strftime("%Y-%m-%d %H:%M:%S"))
            # If we want data, we have to make sure that the range has some data... The inverter seems to not send data to the cloud when not producing...so at night, or early morning we don't have any data
            past = now - timedelta(hours=20)
            data = self.api.get_inverterDetails(self.site_id, self.inverter_id,past.strftime("%Y-%m-%d %H:%M:%S"),now.strftime("%Y-%m-%d %H:%M:%S"))

            inverter_details = data["data"]
        except KeyError as ex:
            raise UpdateFailed("Missing inverter data, skipping update") from ex
        self.data = {}
        self.attributes = {}
        try:
            if "telemetries" in inverter_details:
                if len(inverter_details["telemetries"]) > 0:
                    lastTelemetry=inverter_details["telemetries"][-1]
                    self.data["L1Data_acVoltage"] = lastTelemetry["L1Data"]["acVoltage"]
                    self.data["totalActivePower"] = lastTelemetry["totalActivePower"]
                    self.data["powerLimit"] = lastTelemetry["powerLimit"]
                    self.data["totalEnergy"] = lastTelemetry["totalEnergy"]
                    self.data["inverterMode"] = lastTelemetry["inverterMode"]
                    self.attributes["L1Data_acVoltage"] = {"date": lastTelemetry["date"]}
                    self.attributes["totalActivePower"] = {"date": lastTelemetry["date"]}
                    self.attributes["powerLimit"] = {"date": lastTelemetry["date"]}
                    self.attributes["totalEnergy"] = {"date": lastTelemetry["date"]}
                    self.attributes["inverterMode"] = {"date": lastTelemetry["date"]}
        except KeyError as ex:
            raise UpdateFailed("Missing inverter telemetry data, skipping update") from ex
        LOGGER.debug("Updated SolarEdge inverter details: %s, %s", self.data, self.attributes)


