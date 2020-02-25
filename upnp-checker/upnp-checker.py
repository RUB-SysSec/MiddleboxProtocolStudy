import asyncio
from dataclasses import dataclass

from async_upnp_client import UpnpAction, UpnpError, UpnpFactory, UpnpService
from async_upnp_client.aiohttp import AiohttpRequester
from async_upnp_client.search import async_search


@dataclass
class Forward:
    NewRemoteHost: str
    NewExternalPort: int
    NewProtocol: str
    NewInternalPort: int
    NewInternalClient: str
    NewEnabled: bool
    NewPortMappingDescription: str
    NewLeaseDuration: int

    def __repr__(self):
        return (
            f"{self.NewRemoteHost}:{self.NewExternalPort} -> {self.NewInternalClient}:{self.NewInternalPort}: "
            f"{self.NewPortMappingDescription} (ttl: {self.NewLeaseDuration}, enabled: {self.NewEnabled})"
        )


class UPnPChecker:
    async def check_forwards(self, service: UpnpService):
        act: UpnpAction = service.action("GetGenericPortMappingEntry")
        try:
            for idx in range(1000):
                forward = Forward(**(await act.async_call(NewPortMappingIndex=idx)))
                print(f"  [+] Got forward: {forward}")
        except UpnpError as ex:
            print(f"Finished enumerating, got {idx} forwards")

    async def check_device(self, dev):
        requester = AiohttpRequester()
        factory = UpnpFactory(requester)

        device = await factory.async_create_device(dev["LOCATION"])
        print(
            f"[+] Got device: {device.friendly_name} with {len(device.services)} services"
        )
        for name, service in device.services.items():
            if "WANIPConnection" in name or "WANPPPConnection" in name:
                print(f"[+] Got wan*connection ({name}), checking for forwards..")
                await self.check_forwards(service)
            else:
                print(f"[-] Got {name}")

    async def find_devices(self):
        print("[-] Trying to find upnp:rootdevices..")
        await async_search(
            service_type="upnp:rootdevice", async_callback=self.check_device
        )
        print("[-] We are done.")


if __name__ == "__main__":
    checker = UPnPChecker()
    asyncio.run(checker.find_devices())
