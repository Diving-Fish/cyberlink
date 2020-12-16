import websockets
import asyncio
import functools
import uuid


class CyberError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return f"[Cyber Error] {self.msg}"


class CyberGroup:
    def __init__(self, group_name, link):
        self.name = group_name
        self.link = link
        self.on_recv_funcs = {}
        self.data_parser_func = None
        self.connections = {}

    async def broadcast(self, data):
        for connection in self.connections:
            await connection.send(data)

    def set_recv_func(self, path, func):
        if path in self.on_recv_funcs:
            raise CyberError(f"The on_recv function for path '{path}' has been registered in group {self.name}")
        self.on_recv_funcs[path] = func

    def set_data_parser_func(self, func):
        if self.data_parser_func is not None:
            raise CyberError(f"The data_parser function has been registered in group {self.name}")
        self.data_parser_func = func

    def add_connection(self, connection):
        self.connections[connection.uid] = connection

    def del_connection(self, connection):
        del self.connections[connection.uid]

    def get_connection(self, uid):
        if uid not in self.connections:
            raise CyberError(f"The uid {uid} connection not exists.")
        return self.connections[uid]

    def on_recv(self, path):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            self.set_recv_func(path, func)
            return wrapper
        return decorator

    def parser(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        self.set_data_parser_func(func)
        return wrapper


class CyberLink:
    def __init__(self):
        self.server = None
        self.groups = {"default": CyberGroup("default", self)}
        self.connections = {}
        self.on_connect_funcs = {}

    def start(self, host='localhost', port=5000):
        self.server = websockets.serve(self.main_loop, host=host, port=port)
        asyncio.get_event_loop().run_until_complete(self.server)
        asyncio.get_event_loop().run_forever()

    def create_group(self, group_name):
        if group_name in self.groups:
            raise CyberError(f"The group named {group_name} exists.")
        self.groups[group_name] = CyberGroup(group_name, self)
        return self.groups[group_name]

    def get_group(self, group_name):
        if group_name not in self.groups:
            raise CyberError(f"The group named {group_name} not exists.")
        return self.groups[group_name]

    def get_connection(self, uid):
        if uid not in self.connections:
            raise CyberError(f"The uid {uid} connection not exists.")
        return self.connections[uid]

    def on_recv(self, path):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            self.groups["default"].set_recv_func(path, func)
            return wrapper
        return decorator

    def on_connect(self, path):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            self.on_connect_funcs[path] = func
            return wrapper
        return decorator

    def parser(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        self.groups["default"].set_data_parser_func(func)
        return wrapper

    async def main_loop(self, websocket, path):
        connection = CyberConnection(self, websocket, path)
        self.connections[connection.uid] = connection
        self.get_group("default").add_connection(connection)
        if self.on_connect_funcs[path] is not None:
            await self.on_connect_funcs[path](connection)

        # Set connection then do receive loop
        connection.established = True
        while connection.alive:
            await connection.recv_loop()

    async def send(self, uid, data):
        try:
            if isinstance(uid, str):
                await self.get_connection(uid).send(data)
            else:
                for _uid in uid:
                    await self.get_connection(_uid).send(data)
        except KeyError:
            raise CyberError(f"no connection with uuid {uid}")

    async def broadcast(self, group, data):
        await self.get_group(group).broadcast(data)


class CyberContext:
    def __init__(self, connection, data):
        self.connection = connection
        self.data = data

    async def reply(self, data):
        await self.connection.send(data)

    async def recv(self):
        return await self.connection.recv()


class CyberConnection:
    def __init__(self, link: CyberLink, websocket, path):
        self.link = link
        self.alive = True
        self.established = False
        self.websocket = websocket
        self.group = self.link.get_group("default")
        self.path = path
        self.uid = str(uuid.uuid4())
        self.values = {}

    def close(self):
        self.alive = False

    def set_value(self, key, value):
        self.values[key] = value

    def get_value(self, key):
        return self.values[key]

    def set_group(self, group_name):
        self.group.del_connection(self)
        self.group = self.link.get_group(group_name)
        self.group.add_connection(self)

    async def recv(self):
        raw_data = await self.websocket.recv()
        if self.group.data_parser_func is not None:
            data = self.group.data_parser_func(raw_data)
        else:
            data = raw_data
        return data

    async def recv_loop(self):
        context = CyberContext(self, await self.recv())
        await self.group.on_recv_funcs[self.path](context)

    async def send(self, data):
        await self.websocket.send(data)
