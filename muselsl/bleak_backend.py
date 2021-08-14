import asyncio

from bleak import BleakScanner, BleakClient
from pprint import pprint


async def list_muses_async():
    print("Searching for nearby Muse devices...")
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


async def connect(address):
    client = None
    try:
        client = BleakClient(address)
        await client.connect()
        return client
    except Exception as e:
        print(e)
        if client is not None:
            await disconnect(client)

