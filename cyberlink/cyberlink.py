import websockets
import asyncio
import functools
import uuid


class CyberError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return f"[Cyber Error] {self.msg}"


class CyberLink:
    def __init__(self):
        self.server = None
        self.group = {"default": []}
        self.group_functions = {"default": []}
        self.connections = {}
        self.connect_func = None

    def start(self, host='localhost', port=5000):
        self.server = websockets.serve(self.main_loop, host=host, port=port)
        asyncio.get_event_loop().run_until_complete(self.server)
        asyncio.get_event_loop().run_forever()

    def create_group(self, group_name):
        if group_name not in self.group:
            self.group[group_name] = []
            self.group_functions[group_name] = []

    def on_recv(self, group="default"):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            if isinstance(group, str):
                if group == '*':
                    for _group in self.group_functions.keys():
                        self.group_functions[_group].append(func)
                else:
                    self.group_functions[group].append(func)
            else:
                for _group in group:
                    self.group_functions[_group].append(func)
            return wrapper
        return decorator

    def on_connect(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        self.connect_func = func
        return wrapper

    async def main_loop(self, websocket, _):
        connection = CyberConnection(self, websocket)
        self.connections[connection.uid] = connection
        self.group["default"].append(connection.uid)
        if self.connect_func is not None:
            await self.connect_func(connection)

        # Set connection then do receive loop
        connection.established = True
        while connection.alive:
            await connection.recv()

    async def send(self, uid, data):
        try:
            if isinstance(uid, str):
                await self.connections[uid].send(data)
            else:
                for _uid in uid:
                    await self.send(_uid, data)
        except KeyError:
            raise CyberError(f"no connection with uuid {uid}")

    async def broadcast(self, group, data):
        try:
            for uid in self.group[group]:
                await self.send(uid, data)
        except KeyError:
            raise CyberError(f"no group named {group}")


class CyberContext:
    def __init__(self, connection, data):
        self.connection = connection
        self.data = data
        self.alive = True

    async def reply(self, data):
        await self.connection.send(data)

    def abort(self):
        self.alive = False


class CyberConnection:
    def __init__(self, link: CyberLink, websocket):
        self.link = link
        self.alive = True
        self.established = False
        self.websocket = websocket
        self.group = "default"
        self.uid = str(uuid.uuid4())
        self.values = {}

    def close(self):
        self.alive = False

    def set_value(self, key, value):
        self.values[key] = value

    def get_value(self, key):
        return self.values[key]

    def set_group(self, group):
        self.group = group

    async def recv(self):
        if not self.established:
            return await self.websocket.recv()

        context = CyberContext(self, await self.websocket.recv())
        for func in self.link.group_functions[self.group]:
            await func(context)
            if not context.alive:
                break

    async def send(self, data):
        await self.websocket.send(data)
