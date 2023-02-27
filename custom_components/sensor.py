import aiohttp
import logging
import voluptuous as vol
from datetime import timedelta
from homeassistant.core import callback
from homeassistant.const import CONF_NAME, ATTR_ATTRIBUTION, EVENT_HOMEASSISTANT_START
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers import config_validation as cv
from .const import (
    API_ENDPOINT,
    USER_AGENT,
    DEFAULT_ICON,
    DEFAULT_NAME,
    CONF_GPS_LOC,
    ATTRIBUTION,
)

# ---------------------------------------------------------
# API Documentation
# ---------------------------------------------------------
# https://www.weather.gov/documentation/services-web-api
# https://forecast-v3.weather.gov/documentation
# ---------------------------------------------------------

_LOGGER = logging.getLogger(__name__)
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_GPS_LOC): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):
    """ Configuration from yaml """
    name = config.get(CONF_NAME, DEFAULT_NAME)
    gps_loc = config.get(CONF_GPS_LOC)
    async_add_entities([NWSAlertCoordSensor(name, gps_loc)], True)


async def async_setup_entry(hass, entry, async_add_entities):
    """ Setup the sensor platform. """
    name = entry.data[CONF_NAME]
    gps_loc = entry.data[CONF_GPS_LOC]
    async_add_entities([NWSAlertCoordSensor(name, gps_loc)], True)


class NWSAlertCoordSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, name, gps_loc):
        """Initialize the sensor."""
        self._name = name
        self._icon = DEFAULT_ICON
        self._state = 0
        self._event = None
        self._event_id = None
        self._message_type = None
        self._event_status = None
        self._event_severity = None
        self._event_expires = None
        self._display_desc = None
        self._spoken_desc = None
        self._gps_loc = gps_loc.replace(' ', '')

    @property
    def unique_id(self):
        """
        Return a unique, Home Assistant friendly identifier for this entity.
        """
        return f"{self._name}_{self._name}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state message."""
        attrs = {}

        attrs[ATTR_ATTRIBUTION] = ATTRIBUTION
        attrs['title'] = self._event
        attrs['event_id'] = self._event_id
        attrs['message_type'] = self._message_type
        attrs['event_status'] = self._event_status
        attrs['event_severity'] = self._event_severity
        attrs['event_expires'] = self._event_expires
        attrs['display_desc'] = self._display_desc
        attrs['spoken_desc'] = self._spoken_desc

        return attrs

    async def async_added_to_hass(self):
        """Register callbacks."""
        _LOGGER.debug("Registering: %s...", self.entity_id)

        @callback
        def sensor_startup(event):        
            """Update sensor on startup."""

            self.async_schedule_update_ha_state(True)

        self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_START, sensor_startup
        )        

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        values = await self.async_get_state()
        self._state = values['state']
        self._event = values['event']
        self._event_id = values['event_id']
        self._message_type = values['message_type']
        self._event_status = values['event_status']
        self._event_severity = values['event_severity']
        self._event_expires = values['event_expires']
        self._display_desc = values['display_desc']
        self._spoken_desc = values['spoken_desc']

    async def async_get_state(self):
        values = {
            'state': self._state,
            'event': self._event,
            'event_id': self._event_id,
            'message_type': self._message_type,
            'event_status': self._event_status,
            'event_severity': self._event_severity,
            'event_expires': self._event_expires,
            'display_desc': self._display_desc,
            'spoken_desc': self._spoken_desc
        }

        headers = {'User-Agent': USER_AGENT,
                   'Accept': 'application/ld+json'
                   }

        data = None
        url = '%s/alerts/active/count' % API_ENDPOINT
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as r:
                _LOGGER.debug("getting state for %s from %s" % (self._gps_loc, url))
                if r.status == 200:
                    data = await r.json()
        
        if data is not None:
            # Reset values before reassigning
            values = {
                'state': 0,
                'event': None,
                'event_id': None,
                'message_type': None,
                'event_status': None,
                'event_severity': None,
                'event_expires': None,
                'display_desc': None,
                'spoken_desc': None
            }
            
            values = await self.async_get_alerts()
        return values

    async def async_get_alerts(self):
        values = {
            'state': self._state,
            'event': self._event,
            'event_id': self._event_id,
            'message_type': self._message_type,
            'event_status': self._event_status,
            'event_severity': self._event_severity,
            'event_expires': self._event_expires,
            'display_desc': self._display_desc,
            'spoken_desc': self._spoken_desc
        }

        headers = {'User-Agent': USER_AGENT,
                   'Accept': 'application/geo+json'
                   }
        data = None
        url = '%s/alerts/active?point=%s' % (API_ENDPOINT, self._gps_loc)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as r:
                _LOGGER.debug("getting alert for %s from %s" % (self._gps_loc, url))
                if r.status == 200:
                    data = await r.json()

        if data is not None:
          events = []
          headlines = []
          event_id = ""
          message_type = ""
          event_status = ""
          event_severity = ""
          event_expires = ""
          display_desc = ""
          spoken_desc = ""
          features = data["features"]
          for alert in features:
              event = alert["properties"]["event"]
              if "NWSheadline" in alert["properties"]["parameters"]:
                  headline = alert["properties"]["parameters"]["NWSheadline"][0]
              else:
                  headline = event

              id = alert["id"]
              type = alert["properties"]["messageType"]
              status = alert['properties']['status']
              description = alert["properties"]["description"]
              instruction = alert["properties"]["instruction"]
              severity = alert["properties"]["severity"]
              certainty = alert["properties"]["certainty"]
              expires = alert["properties"]["expires"]

              # if event in events:
              #    continue

              events.append(event)
              headlines.append(headline)

              if display_desc != "":
                  display_desc += "\n\n-\n\n"

              display_desc += (
                  "\n>\nHeadline: %s\nStatus: %s\nMessage Type: %s\nSeverity: %s\nCertainty: %s\nExpires: %s\nDescription: %s\nInstruction: %s"
                  % (headline, status, type, severity, certainty, expires, description, instruction)
              )

              if event_id != "":
                  event_id += ' - '

              event_id += id
            
              if message_type != "":
                     message_type += ' - '

              message_type += type
            
              if event_status != "":
                     event_status += ' - '

              event_status += status
            
              if event_severity != "":
                     event_severity += ' - '

              event_severity += severity
            
              if event_expires != "":
                     event_expires += ' - '

              event_expires += expires
            
          if headlines:
              num_headlines = len(headlines)
              i = 0
              for headline in headlines:
                  i += 1
                  if spoken_desc != "":
                      if i == num_headlines:
                          spoken_desc += "\n\n-\n\n"
                      else:
                          spoken_desc += "\n\n-\n\n"

                  spoken_desc += headline
  
          if len(events) > 0:
              event_str = ""
              for item in events:
                  if event_str != "":
                      event_str += " - "
                  event_str += item

              values["state"] = len(events)
              values["event"] = event_str
              values["event_id"] = event_id
              values["message_type"] = message_type
              values["event_status"] = event_status
              values["event_severity"] = event_severity
              values["event_expires"] = event_expires
              values["display_desc"] = display_desc
              values["spoken_desc"] = spoken_desc
          else:
              values = {
                  "state": 0,
                  "event": None,
                  "event_id": None,
                  "message_type": None,
                  "event_status": None,
                  "event_severity": None,
                  "event_expires": None,
                  "display_desc": None,
                  "spoken_desc": None,
              }

        return values

