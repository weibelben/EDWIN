# EDWIN

Everything is achievable through technology; better living, robust health, and for the first time in human history, ~~the possibility of world peace~~ overly complex home automation and domotics.

-- Howard Stark

## Backup and Restore

An automated backup of Edwin's consciousness is generated once per week. 
5 rolling copies are saved locally and uploaded to Google Drive.

When restoring to an automated backup fails, manual OS restoration
can be performed by following 
[these instructions](https://support.nabucasa.com/hc/en-us/articles/25162566451485-Resetting-Home-Assistant-Green-using-an-SD-card).
A 128GB SD card is taped to the top of Edwin's case in my server room.

### GitHub Version Control

Edwin's configuration, automations, dashboards and some other custom
code are backed up to [my GitHub](https://github.com/weibelben/EDWIN).
A personal access token is stored in `config/secrets.yaml` (.gitignore'd)
and referenced by `config/configuration.yaml`.

```shell
github_token: "ghp_abc123"
```

## Remote Access

### VPN Route to Internal HA URL

Home Assistant is reachable via its internal URL http://192.168.0.x:8123,
assuming one is connected to the same network as the HA server. This can be
achieved remotely via any VPN connection.

### Tailscale

Using the [Tailscale Home Assistant Community Add-on](https://github.com/hassio-addons/addon-tailscale)
one is able to conect to Home Assistant directly, without a VPN. The creation of
a tailnet and inclusion of Home Assistant as one of the machines allows access
to HA from any of the other connected machines via the External machine URL
exposed by HA on the tailnet http://100.x.x.x:8123/.

### Remote Location Sharing

For continuous location sharing, the Home Assistant Companion App requires
constant access to the Home Assistant server and mobile location access at all
times. Location permissions are granted through mobile device app permissions.
Constant access to HA is achievable using Tailscale. 

Maintain a persistent mobile connection to the HA tailnet. Toggle `Use Tailscale DNS`
off so only traffic intended for Home Assistant passes through the Tailscale
connection. Then (android only) ensure that Split Tunneling is enabled for all
apps other thatn Home Assistant. Here is the HA Companion App Server Connection Info

```yaml
# Remote Tailscale URL
Home Assistant URL: http://100.x.x.x:8123/

# Home Network WiFi SSID
Home Network: <Name of home WiFi network>

# HA Internal URL (could be http://homeassistant.local:8123)
Internal Connection URL: http://192.168.0.x:8123
```

## Problem Child Integrations

### Custom CSV Parser

I wrote a CSV parser and attached it as a homeassistant project to my
configuration.yaml. It reads manually entered water usage and cost
data from a csv. The file itself can only contain 10 lines due
to a limitation in the `custom:apexcharts-card`. All historical water
use data is maintainted separately. I update these files every time I
receive a bill from Coal Creek Utility District. 

[EyeOnWater](https://github.com/kdeyev/eyeonwater) is a common
integration to gather water usage metrics but it requires that your
local water provider upload data to BEACON Advanced Metering
Analytics via a Badger Meter smart meter. I emailed CCUD Oct 2025.
So far no response.

### Opower

[Opower](https://www.home-assistant.io/integrations/opower/) is
used in tandem with my Puget Sound Energy (PSE) credentials to
track the usage and cost of natural gas and electricity since the
inception of my utility contract with PSE.

The API endpoint that returns gas and electricity cost per month changed
in October of 2022 and Opower has not updated to match, rendering the
data incomplete. Here is a relevant 
[github issue](https://github.com/tronikos/opower/issues/56).

### World Air Quality Index (WAQI)

[WAQI](https://www.home-assistant.io/integrations/waqi/) 
is used to determine the AQI of the air local to my home.
Data points are used for a number of automations.
Ex. gate whether to turn on bathroom exhaust fans
when the air quality inside is detected as poor/unhealthy with the intent
replace indoor air with clean air from outside.

This integration requires an API token that must be refreshed (recreated)
every 18 months from [Air Quality Open Data Platform's website](https://aqicn.org/data-platform/token/).

### HZA using SLZB06 ZigBee Coordinator

The Home Assistant side of this integration works excellently! The trouble Edwin
was hitting was related to power cycling (ex. local power outages). When my
Synology RT2600ac router rebooted, it would reassign the IP address assigned to
its ethernet ports, leading to my SLZB06 changing IP addresses. ZHA would then 
fail to initialze using the previous IP address, leaving my ZigBee devices
unreachable. To solve this, I added a DHCP reservation on my router, assigning
the ZigBee coordinator's MAC address the static IP of `192.168.0.40`. 

While I was at it, I added a reservation pinning Home Assistant to `192.168.0.236`.
