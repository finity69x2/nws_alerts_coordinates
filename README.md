Alerts from the US National Weather Service (nws_alerts_coordinates)

An updated version of the nws_alerts custom integration for Home Assistant originally found at github.com/finity69x2/nws_alerts

This version will allow the user to use a precise GPS coordinate to get alerts for that specific location.

This integration retrieves updated weather alerts every minute from the US NWS API.

The integration presents the number of currently active alerts as the state of the sensor and lists many alert details as a list in the attributes of the sensor.

Installation:

Manually:

Clone the Repository and copy the "nws_alerts_coordinats" directory to your "custom_components" directory in your config directory

<config directory>/custom_components/nws_alerts_coordinates/...

HACS:

THIS IS CONSIDERED A MORE ADVANCED INTEGRATION AND CAN ONLY BE INSTALLED AND CONFIGURED MANUALLY. THIS IS BECAUSE THE LOCATION USED IS VERY SPECIFIC AND I CAN'T BE SURE IF THE ALERTS WILL BE TIMELY ENOUGH TO GIVE ENOUGH ADVANCED WARNING FOR SEVERE WEATHER.
  
USE AT YOUR OWN RISK!!
  
After installing the integration you can then configure it using the instructions in the following section.

Configuration:

Manually via an entry in your configuration.yaml file:

To create a sensor instance add the following configuration to your sensor definitions using the GPS coordinates for your location:

- platform: nws_alerts_coordinates
  gps_loc: '40.813274031868524,-86.54172988854643' # in format of 'latitute,longitude'

After you restart Home Assistant then you should have a new sensor called "sensor.nws_alerts_coordinates" in your system.

You can override the sensor default name ("sensor.nws_alerts") to one of your choosing by setting the "name:" option:

- platform: nws_alerts_coordinates
  gps_loc: '40.813274031868524,-86.54172988854643' # in format of 'latitute,longitude'
  name: My NWS Alerts Sensor

Using the configuration example above the sensor will then be called "sensor.my_nws_alerts_sensor"
