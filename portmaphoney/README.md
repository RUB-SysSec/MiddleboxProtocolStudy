# UPnP IGD Honeypöttchen

A very basic UPnP IGD honeypot implementing parts of the `WAN*Connection` interfaces of the Internet Gateway Device (IGD) suite. Used for tracking its misuse for port mapping injections.

For the related paper, see *On Using Application-Layer Middlebox Protocols for Peeking Behind NAT Gateways* published in [Network and Distributed Systems Security (NDSS) Symposium 2020](https://www.ndss-symposium.org/ndss2020/).
The paper is available [here](https://www.syssec.ruhr-uni-bochum.de/research/publications/middlebox-protocols/)

The functionality offered by this honeypot consists of three parts:
1. SSDP discovery protocol
2. `WAN*Connection` interface listening on multiple ports and service locations.

## Features

* SSDP (UDP) payload for 1900 requests (responds to any M-SEARCH requests by sending `upnp:rootdevice`, `WANIPConnection:1`, and `WANPPPConnection:1` responses back)
  * Limited to 2 responses per address per hour

* Answers only to SCD requests on specific paths and ports (top lists from analyses, see [ssdppot/const.py](ssdppot/const.py) for ports and paths)

* Supports only enumerating and adding mappings
  * Only the most commonly seen paths are responded with a non-error
  * AddPortMapping succeeds everytime with a plain success message (from miniupnpd)
  * GetPortMapping allows enumerating the first few entries, responding with randomly generated ports

* Stores requests into a mongodb database.

## Install

```
$ pip install -e .
```

* Note: this has only been tested with aiohttp 3.4.4 and may not work with other versions due how to multi-port hosting is implemented.

## Usage

You likely want to save the incoming requests in a PCAP, just in case. Executing `ssdppot tcpdump` prints out a filter capturing all the relevant data.

To launch, simply execute the the `ssdppot run` command, which will start both SSDP responder as well as the SOAP endpoint listeners.

If connstring and database are not defined, `mongodb://localhost` is used for connection and the requests are stored in `ssdppot` collection.

If you only want to track only SSDP requests, you can use `udpresponder` alone.

```
Usage: ssdppot [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  run      Start the honeypot
  tcpdump  Dump command-line options for tcpdump
```
