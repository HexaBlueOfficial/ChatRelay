import discord
import discord_slash as interactions
import openhivenpy as hiven
import json
import aiohttp
import typing
from discord.ext import commands

with open("./token.json") as tokenfile:
    token = json.load(tokenfile)

dbot = commands.Bot(command_prefix=commands.when_mentioned, intents=discord.Intents.all())
hbot = hiven.UserClient()
slash = interactions.SlashCommand(dbot, sync_commands=True, sync_on_cog_reload=True)
dbot.remove_command("help")

@dbot.event
@hbot.event()
async def on_ready():
    channel = dbot.get_channel(832677639944667186)
    room = hbot.get_room("281907503610984307")

    await channel.send(f"**ChatRelay (Discord)** is ready and running on **discord-py-interactions v{interactions.__version__}!**")
    await room.send(f"**ChatRelay (Hiven)** is ready and running on **openhiven.py v{hiven.__version__}!**")

async def htdrelay(ctx: hiven.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://chrl.hexa.blue/api/relays") as response:
            relays: typing.List[dict] = await response.json()
        for relay in relays:
            if relay["hiven"]["room"] == ctx.room.id:
                async with session.post("https://chrl.hexa.blue/api/relays/get_by_room", json={
                    "room": ctx.room.id
                }) as response:
                    relayx: dict = await response.json()
                break

    if relayx is None:
        return

    channel: discord.TextChannel = dbot.get_channel(int(relayx["discord"]["channel"]))
    await channel.send(f"**{ctx.author.name} (@{ctx.author.username}):** {ctx.content}")

async def dthrelay(ctx: discord.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://chrl.hexa.blue/api/relays") as response:
            relays: typing.List[dict] = await response.json()
        for relay in relays:
            if int(relay["discord"]["channel"]) == ctx.channel.id:
                async with session.post("https://chrl.hexa.blue/api/relays/get_by_channel", json={
                    "channel": str(ctx.channel.id)
                }) as response:
                    relayx: dict = await response.json()
                break

    if relayx is None:
        return

    room: hiven.TextRoom = hbot.get_room(relayx["hiven"]["room"])
    await room.send(f"**{str(ctx.author)}:** {ctx.content}")

async def hsetup(ctx: hiven.Message):
    async with aiohttp.ClientSession(headers={"auth": token["chatrelay"]["api"]}) as session:
        if ctx.author.id == ctx.house.owner.id:
            async with session.get("https://chrl.hexa.blue/api/relays") as response:
                relays: typing.List[dict] = await response.json()

            halreadyrelayed = False
            for relay in relays:
                if relay["hiven"]["house"] == ctx.house.id:
                    halreadyrelayed = True
                    break

            if not halreadyrelayed:
                await ctx.room.send("Please state the **name** or **ID** of your Discord server.\nYou can say `abort` anytime to stop the setup.")

                passed0 = False
                while not passed0:
                    args0, _ = await hbot.wait_for("message_create")
                    waitfor0: hiven.Message = args0[0]

                    if waitfor0.author.id == ctx.author.id:
                        passed0 = True

                if waitfor0.content == "abort":
                    await ctx.room.send("Operation aborted.")
                    return

                try:
                    guildid = int(waitfor0.content)
                    guild = discord.utils.get(dbot.guilds, id=guildid)
                except:
                    guild = discord.utils.get(dbot.guilds, name=waitfor0.content)
                finally:
                    if guild is None:
                        await ctx.room.send("Couldn't find a server with that name or ID.\nMake sure you have added the **ChatRelay Discord bot**.\nOperation aborted. Run the command again.")
                    else:
                        galreadyrelayed = False
                        for relay in relays:
                            if relay["discord"]["guild"] == guild.id:
                                galreadyrelayed = True
                                break

                        if not galreadyrelayed:
                            await ctx.room.send("Please state the **name** or **ID** of the **Discord channel** where you want the messages to be relayed.")

                            passed1 = False
                            while not passed1:
                                args1, _ = await hbot.wait_for("message_create")
                                waitfor1: hiven.Message = args1[0]

                                if waitfor1.author.id == ctx.author.id:
                                    passed1 = True

                            if waitfor1.content == "abort":
                                await ctx.room.send("Operation aborted.")
                                return

                            try:
                                channelid = int(waitfor1.content)
                                channel = discord.utils.get(guild.text_channels, id=channelid)
                            except:
                                channel = discord.utils.get(guild.text_channels, name=waitfor1.content)
                            finally:
                                if channel is None:
                                    await ctx.room.send("Couldn't find a channel with that name or ID.\nMake sure that the **ChatRelay Discord bot** can see it!\nOperation aborted. Run the command again.")
                                else:
                                    await session.post("https://chrl.hexa.blue/api/relays", json={
                                        "discord": {
                                            "guild": str(guild.id),
                                            "channel": str(channel.id)
                                        },
                                        "hiven": {
                                            "house": ctx.house.id,
                                            "room": ctx.room.id
                                        }
                                    })
                                    await ctx.room.send("Setup successful! Messages sent in the Discord channel will now be relayed here.\nMeant to set a different room? Go run `+here` in it!")
                        else:
                            await ctx.room.send("A Relay already exists for this server.")
            else:
                await ctx.room.send("You already have a Relay for this House.")
        else:
            await ctx.room.send("You must be the Owner of this House.")

async def hhere(ctx: hiven.Message):
    async with aiohttp.ClientSession(headers={"auth": token["chatrelay"]["api"]}) as session:
        await session.patch("https://chrl.hexa.blue/api/relays/edit_room_by_house", json={
            "house": ctx.house.id,
            "room": ctx.room.id
        })

    await ctx.room.send(f"Relay Room changed to {ctx.room.name}!")

async def invitereq(ctx: hiven.Message):
    if "hiven.house/" in ctx.content:
        flamey = hbot.get_private_room("277398862899966121")
        await flamey.send("A user just requested the Bot to be added to their House!")

@hbot.event()
async def on_message_create(msg: hiven.Message):
    if msg.content.startswith("+"):
        if msg.content.lstrip("+").startswith("setup"):
            await hsetup(msg)
        if msg.content.lstrip("+").startswith("here"):
            await hhere(msg)
    else:
        if isinstance(msg.room.type, (hiven.PrivateRoom, hiven.PrivateGroupRoom)):
            await invitereq(msg)
        else:
            await htdrelay(msg)

@slash.slash(name="setup", description="Sets up the Relay for this server.")
@commands.has_permissions(administrator=True)
async def dsetup(ctx: interactions.SlashContext):
    await ctx.send("You can only run setup via Hiven! Go on the platform and run `+setup`!")

@slash.slash(name="here", description="Sets the Relay channel to this one!")
@commands.has_permissions(administrator=True)
async def dhere(ctx: interactions.SlashContext):
    async with aiohttp.ClientSession(headers={"auth": token["chatrelay"]["api"]}) as session:
        await session.patch("https://chrl.hexa.blue/api/relays/edit_channel_by_guild", json={
            "guild": ctx.guild.id,
            "channel": ctx.channel.id
        })

    await ctx.send(f"Relay Channel changed to {ctx.channel.name}!")

@dbot.event
async def on_message(msg: discord.Message):
    await dthrelay(msg)

hbot.run(token["chatrelay"]["hiven"])
dbot.run(token["chatrelay"]["discord"])