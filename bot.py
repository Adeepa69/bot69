import discord
from discord import app_commands
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)

# Sync all app commands to Discord



@tree.command(name="hello", description="Says hello to you")
async def hello(interaction: discord, text: str):
    await interaction.response.send_message(text)


@tree.command(name="clear", description="Clears the chat by how many messages you specify")
async def clear(interaction: discord, amount: int):
    # We need to validate the user's permissions that they have the manage_messages permission
    if interaction.user.guild_permissions.manage_messages:
        await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"Cleared {amount} messages", ephemeral=True)
    else:
        await interaction.response.send_message('fuck you', ephemeral=False)


# Make a command that sets a server's message history, i.e. the time a message can last before the bot deletes it
# automatically
@tree.command(name="message_history", description="Sets the length of how long messages should last in your server")
async def history(interaction: discord, length: int):
    # Check that the use has the administrator permission to use it
    if interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(f"Set the message history of this server to {length} days",
                                                ephemeral=True)
    else:
        duration = timedelta(minutes=30)
        expiration_time: datetime = discord.utils.utcnow() + duration
        await interaction.user.timeout(expiration_time)


@client.event
async def on_ready():
    await tree.sync()
    print(f'We have logged in as {client.user}')


client.run(open('token', 'r').read())
