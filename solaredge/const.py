"""Constants for the SolarEdge Monitoring API."""
from datetime import timedelta
import logging

# domain needs to be the same as the one in manifest.json.
# it also need to be the same as the folder name, otherwise the strings.json will not be found
# it has also to be the same as the folder name of brand (to be able to fetch the logo)
DOMAIN = "solaredge"

LOGGER = logging.getLogger(__package__)

DATA_API_CLIENT = "api_client"

# Config for solaredge monitoring api requests.
CONF_SITE_ID = "site_id"
CONF_INVERTER_ID = "inverter_id"
DEFAULT_NAME = "SolarEdge Inverter"

INVERTER_UPDATE_DELAY = timedelta(minutes=5)

#SCAN_INTERVAL = timedelta(minutes=15)
