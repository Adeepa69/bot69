import os
import discord
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)


@tree.command(name="hello", description="Says hello to you")
async def hello(interaction: discord, test: str):
    await interaction.response.send_message(test)


@client.event
async def on_ready():
    await tree.sync()
    print(f'We have logged in as {client.user}')


# @client.event
# async def on_message(message):
#     if message.author == client.user:
#         return
#
#     if message.content.startswith('$hello'):
#         await message.reply('Hello!', mention_author=False)


client.run(os.environ.get("Discord"))
