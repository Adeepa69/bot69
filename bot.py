import discord
import json
from discord import app_commands
from discord.ext import tasks
from datetime import datetime, timedelta

# Define normal Discord stuff
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)

# Dictionary that determines how long messages should last in the server
# Read from server_policy file and store it in a dictionary
with open('server_policy', 'r') as file:
    # Convert the string to a dictionary
    server_policy = eval(file.read())

print(server_policy)

# Run this task every hour and run functions inside the main function below this decorator
@tasks.loop(hours=1)
# Write to server-policy file as backup
async def backup_server_policy():
    with open('server_policy', 'w') as policy_file:
        policy_file.write(json.dumps(server_policy))


# Clean up messages
async def clear_messages():
    # Check server_policy for the message history of each server
    for server in server_policy:
        # Get the server object
        guild = client.get_guild(server)
        # Loop through each text channel, making sure to leave out voice channels, forums and announcements
        for channel in guild.text_channels:
            # Purge the channel by the message history, but we need a function to check whether to delete the message
            await channel.purge(limit=10, check=check)


# Check the message is older than the set amount of days
def check(message: discord.Message):
    # Get the server object
    guild = message.guild
    # Get the message history of the server
    history_policy = server_policy[guild.id]
    # Get the time the message was sent
    time = message.created_at
    # Get the current time
    now = discord.utils.utcnow()
    # Check if the message was sent before the message history
    if (now - time).days > history_policy:
        return True
    else:
        return False


# Simple slash command
@tree.command(name="hello", description="Says hello to you")
async def hello(interaction: discord, text: str):
    await interaction.response.send_message(text)


# /clear command
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
        # Add the server id to dictionary and set the message_history alongside it
        server_policy.update({interaction.guild.id: length})
        await interaction.response.send_message(f"Set the message history of this server to {length} days",
                                                ephemeral=True)
    else:
        duration = timedelta(minutes=30)
        expiration_time: datetime = discord.utils.utcnow() + duration
        await interaction.user.timeout(expiration_time)


# Runs as soon as the code is ready
@client.event
async def on_ready():
    await tree.sync()
    print(f'We have logged in as {client.user}')


client.run(open('token', 'r').read())
