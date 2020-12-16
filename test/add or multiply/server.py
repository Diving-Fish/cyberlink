from cyberlink import CyberLink, CyberContext, CyberConnection
import re

link = CyberLink()
group_add = link.create_group("add")
group_multiply = link.create_group("multiply")


@link.on_connect("/")
async def on_connect(conn: CyberConnection):
    message = await conn.recv()
    group = re.match("I want to join group (.+)", message).groups()[0]
    conn.set_group(group)


@group_add.on_recv("/")
async def add(ctx: CyberContext):
    data = ctx.data.split(' ')
    await ctx.reply(str(int(data[0]) + int(data[1])))


@group_multiply.on_recv("/")
async def multiply(ctx: CyberContext):
    data = ctx.data.split(' ')
    await ctx.reply(str(int(data[0]) * int(data[1])))


link.start()
