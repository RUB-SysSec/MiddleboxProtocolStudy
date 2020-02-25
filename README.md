# On Using Application-Layer Middlebox Protocols for Peeking Behind NAT Gateways

This repository contains auxiliary material for the paper "On Using Application-Layer Middlebox Protocols for Peeking Behind NAT Gateways" published at [26th Annual Network and Distributed System Security Symposium (NDSS)](https://www.ndss-symposium.org/ndss2020/), San Diego, California, 23 - 26 February 2020.

* [UPnP IGD honeypot implementation](portmaphoney/)
* [UPnP Checker](upnp-checker/) - a tool to check for local upnp devices and existing port forwards on IGD devices


# Abstract ([Full paper](https://www.syssec.ruhr-uni-bochum.de/research/publications/middlebox-protocols/))

> Typical port scanning approaches do not achieve a
full coverage of all devices connected to the Internet as not all
devices are directly reachable via a public (IPv4) address: due to
IP address space exhaustion, firewalls, and many other reasons,
an end-to-end connectivity is not achieved in today’s Internet
anymore. Especially Network Address Translation (NAT) is widely
deployed in practice and it has the side effect of “hiding” devices
from being scanned. Some protocols, however, require end-to-end
connectivity to function properly and hence several methods were
developed in the past to enable crossing network borders.
> 
> In this paper, we explore how an attacker can take advantage
of such application-layer middlebox protocols to access devices
located behind these gateways. More specifically, we investigate
different methods for identifying such devices by using only
legitimate protocol features. We categorize the available protocols
into two classes: First, there are persistent protocols that are
typically port-forwarding based. Such protocols are used to allow
local network devices to open and forward external ports to them.
Second, there are non-persistent protocols that are typically proxy-
based to route packets between network edges, such as HTTP
and SOCKS proxies. We perform a comprehensive, Internet-wide
analysis to obtain an accurate overview of how prevalent and
widespread such protocols are in practice. Our results indicate
that hundreds of thousands of hosts are vulnerable for different
types of attacks, e. g., we detect over 400,000 hosts that are
likely vulnerable for attacks involving the UPnP IGD protocol.
More worrisome, we find empirical evidence that attackers are
already actively exploiting such protocols in the wild to access
devices located behind NAT gateways. Amongst other findings,
we discover that at least 24 % of all open Internet proxies are
misconfigured to allow accessing hosts on non-routable addresses.
