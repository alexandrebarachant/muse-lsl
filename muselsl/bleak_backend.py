import asyncio

from bleak import BleakScanner
from pprint import pprint


async def list_muses_async():
    devices = await BleakScanner.discover()
    muses = []
    for d in devices:
        if "Muse" in d.name:
            muses.append(d)
    return muses


def list_muses():
    return asyncio.get_event_loop().run_until_complete(
        list_muses_async()
    )

