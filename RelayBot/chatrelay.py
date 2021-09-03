import discord
import openhivenpy as hiven
import json
import discord_slash as interactions
import tracemalloc
import typing
from discord.ext import commands

with open("./token.json") as tokenfile:
    token = json.load(tokenfile)
with open("./relays.json") as relaysfile:
    relays = json.load(relaysfile)
with open("./ChatRelay/RelayBot/misc/assets/embed.json") as embedfile:
    embed = json.load(embedfile)

dbot = commands.Bot(command_prefix=commands.when_mentioned_or("+", "cr!"), intents=discord.Intents.all())
hbot = hiven.UserClient(token=token["chatrelay"]["hiven"])
slash = interactions.SlashCommand(dbot, sync_commands=True, sync_on_cog_reload=True)
dbot.remove_command("help")

tracemalloc.start()

@dbot.event
@hbot.event()
async def on_ready():
    channel = dbot.get_channel(832677639944667186)
    room = hbot.get_room(281907503610984307)

    await channel.send(f"**ChatRelay (Discord)** is ready and running on **discord.py v{discord.__version__}!**")
    await room.send(f"**ChatRelay (Hiven)** is ready and running on **openhiven.py v{hiven.__version__}!**")

@hbot.event()
async def on_message_create(msg: hiven.Message):
    if msg.content.startswith("+"):
        if "setup" in msg.content:
            await msg.room.send("Please state the **name** or **ID** of your Discord server.")

            waitfor = await hbot.wait_for("message_create")