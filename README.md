# SolarEdge Inverter Integration for Home Assistant
This repo contains my custom integration for Home Assistant for a mono-phased SolarEdge inverter.

I've developed this integration to be able to monitor overvoltage and inverter mode, because a lot of people have installed solar panels in my street, and I regularly see the inverter limiting itself to avoid overvoltage.
Note that it is not better or worse than the official integration...it is just different as it provides different details.

What is the difference compared to the official SolarEdge integration?
-instead of focusing on the site, this integration focuses on the inverter itself
-it uses only one type of API call, but it is done more frequently
-it has the following sensors:
 -Voltage AC
 -Active power
 -Lifetime energy
 -Power limit
 -Inverter mode

Note: Instead of using the python library solaredge==0.0.2 like the official integration, it embeds its own improved copy of the library with the call to Inverter Technical Data.

Known limitations:
-It only works with mono-phase inverters... but feel free to improve it by extracting the (see https://knowledge-center.solaredge.com/sites/kc/files/se_monitoring_api.pdf for details on API response)
-It has been tested only with one inverter... but I suppose that it will work with most mono-phased inverters

To install it, copy the "solardge" folder to <home_assistant_config_folder>/custom_components
Then restart Home Assistant (just to be sure) and add the "SolarEdge" integration.
