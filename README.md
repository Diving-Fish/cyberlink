# cyberlink
A light, asynchronous websocket server written by Python.

## Install

Python >= 3.7

```sh
pip install -i https://test.pypi.org/simple/ cyberlink==0.1.0.dev2
```

## Quick Start

Server side:
```python
from cyberlink import CyberLink, CyberContext

link = CyberLink()


@link.on_recv()
async def echo(ctx: CyberContext):
    await ctx.reply(ctx.data)


link.start(port=5000)
```

Corresponding client:
```python
import asyncio
import websockets


async def hello():
    uri = "ws://localhost:5000"
    async with websockets.connect(uri) as websocket:
        for i in range(3):
            print(f"> {i}")
            await websocket.send(str(i))
            print(f"< {await websocket.recv()}")


asyncio.get_event_loop().run_until_complete(hello())
```
