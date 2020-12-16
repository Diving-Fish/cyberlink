#!/usr/bin/env python

# WS client example

import asyncio
import websockets


async def add():
    uri = "ws://localhost:5000"
    async with websockets.connect(uri) as websocket:
        await websocket.send("I want to join group add")
        await websocket.send("10 20")
        print(await websocket.recv())


asyncio.get_event_loop().run_until_complete(add())
