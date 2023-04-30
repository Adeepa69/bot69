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


@tree.command(name="clear", description="Clears the chat by how many messages you specify")
async def clear(interaction: discord, amount: int):
    # We need to validate the user's permissions that they have the manage_messages permission
    if interaction.user.guild_permissions.manage_messages:
        await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"Cleared {amount} messages", ephemeral=True)
    else:
        await interaction.response.send_message('fuck you', ephemeral=False)


@client.event
async def on_ready():
    await tree.sync()
    print(f'We have logged in as {client.user}')


client.run(os.environ.get("Discord"))
