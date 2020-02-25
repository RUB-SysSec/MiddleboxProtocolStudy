from string import Template

from .common import read_data_file

# 404 headers
# < HTTP/1.1 404 Not Found
# < SERVER: Linux/2.6.21, UPnP/1.0, Portable SDK for UPnP devices/1.3.1
# < CONNECTION: close
# < CONTENT-LENGTH: 48
# < CONTENT-TYPE: text/html
ERROR_HEADERS = {
    "SERVER": "Linux/2.6.21, UPnP/1.0, Portable SDK for UPnP devices/1.3.1",
    "CONNECTION": "close",
    #'CONTENT-LENGTH': '48',  # gets automatically calculated by aiohttp
    "CONTENT-TYPE": "text/html",
    "X-User-Agent": "redsonic",
}

# HTTP/1.1 200 OK
SSDP_WEB_HEADERS = {
    "CONTENT-TYPE": "text/xml",
    "DATE": "Sun, 09 Dec 2018 07:57:07 GMT",
    "LAST-MODIFIED": "Sat, 01 Jan 2000 00:00:01 GMT",
    "SERVER": "Linux/2.6.21, UPnP/1.0, Portable SDK for UPnP devices/1.3.1",
    "X-User-Agent": "redsonic",
    "CONNECTION": "close",
}
SSDP_WEB_RESPONSE = read_data_file("ssdp_response_tenda.txt")

SSDP_MAPPING_HEADERS = {
    #'CONTENT-LENGTH': 626,  # gets automatically calculated by aiohttp
    "CONTENT-TYPE": 'text/xml; charset="utf-8"',
    "DATE": "Sun, 09 Dec 2018 08:03:25 GMT",
    "EXT": "",
    "SERVER": "Linux/2.6.21, UPnP/1.0, Portable SDK for UPnP devices/1.3.1",
    "X-User-Agent": "redsonic",
}
SSDP_MAPPING_RESPONSE = Template(read_data_file("ssdp_mapping_response.txt"))

SSDP_MAPPING_END_HEADERS = SSDP_WEB_HEADERS
SSDP_MAPPING_END = read_data_file("ssdp_mapping_end.txt")

SSDP_ADD_MAPPING_RESPONSE = read_data_file("ssdp_add_mapping_response_miniupnpd.txt")
# Reuse the same headers as for mapping list..
SSDP_ADD_MAPPING_HEADERS = SSDP_MAPPING_HEADERS

# Port, number of hosts
HTTP_PORTS = {
    5431: 0,
    2048: 0,
    49152: 0,
    52869: 0,
    5500: 0,
    5555: 0,
    49153: 0,
    49154: 0,
    3183: 0,
    55567: 0,
    4996: 0,
    1900: 0,
    4409: 0,
    54147: 0,
    4427: 0,
    5000: 0,
    8080: 0,
    35510: 0,
    3642: 0,
    38947: 0,
    34948: 0,
    49600: 0,
    4097: 0,
    3278: 0,
    42833: 0,
    3091: 0,
    50000: 0,
    3885: 0,
    18888: 0,
    49155: 0,
    49125: 0,
    37215: 0,
    1901: 0,
    5556: 0,
    49157: 0,
}


# Some examples from the internet-wide scans
CTL_PATHS = [
    "/upnp/control/WANIP{tail:.+?}",
    "/ctl/IPConn",
    "/etc/linuxigd/gateconnSCPD.ctl",
    "/upnp/control/WANPPP{tail:.+?}",
    "/upnp/control/WANIPConnection{tail:.+?}",
    "/upnp/control{tail:.+?}",
    "/upnp/control/WAN:{tail:.+}",
    "/uuid:{tail:.+}",
    "/upnp{tail:.+}",
    "/UD{tail:.+}",
    "/WAN{tail:.+}",
    "/control{tail:.+?}",
    "/ctrlt{tail:.+?}",
]

# respond to the following addreses
SCD_PATHS = [
    "/etc/linuxigd/gatedesc.xml",
    "/gatedesc.xml",
    "/RootDesc.xml",
    "/rootDesc.xml",
    "/pcsDesc.xml",
    "/IGDdevicedesc.xml",
    "/DeviceDescription.xml",
    "/desc.xml",
    "/igdevicedesc.xml",
    "/dyndev/picsdesc.xml",
    "/gatedesc_{tail:.+}",
    "/dyndev/{tail:.+}",
    "/trdesc.xml",
    "/tr064dev.xml",
    "/IGD.xml",
    "/RootDeviceDesc.xml",
    "/devicedesc.xml",
]
