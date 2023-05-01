import asyncio
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import tasks

# Define normal Discord stuff
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)

# If there is no dictionary, then create one to prevent errors
try:
    # Dictionary that determines how long messages should last in the server
    # Read from server_policy file and store it in a dictionary
    with open('server_policy', 'r') as file:
        # Convert the string to a dictionary
        server_policy = eval(file.read())
except FileNotFoundError:
    server_policy = {}
except SyntaxError:
    server_policy = {}


# Run this task every hour and run functions inside the main function below this decorator
@tasks.loop(hours=1)
async def hourly_schedule():
    await asyncio.gather(backup_server_policy(), clear_messages())


# Write to server-policy file as backup
async def backup_server_policy():
    with open('server_policy', 'w') as policy_file:
        policy_file.write(str(server_policy))


# Clean up messages
async def clear_messages():
    # Check server_policy for the message history of each server
    for server in server_policy:
        # Get the server object
        guild = client.get_guild(server)
        # If no servers have a message history, then return
        if guild is None:
            return
        else:
            # Loop through each text channel, making sure to leave out voice channels, forums and announcements
            for channel in guild.text_channels:
                # Purge the channel by the message history
                await channel.purge(limit=100, check=check)


# Check the message is older than the set number of days
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
        await interaction.response.send_message(f"Cleaning up {amount} messages, hold tight!", ephemeral=True)
        await interaction.channel.purge(limit=amount)
    else:
        await interaction.response.send_message('fuck you', ephemeral=False)


# Make a command that sets a server's message history, i.e. the time a message can last before the bot deletes it
# automatically
@tree.command(name="disappearing_messages", description="Sets the length of how long messages should last in your "
                                                        "server")
async def history(interaction: discord, length: int):
    # Check that the use has the administrator permission to use it
    if interaction.user.guild_permissions.administrator:
        # Check if the user is asking for an unreasonable length of time (longer than 14 days)
        if length > 14:
            # Add the server id to dictionary and set the message_history alongside it
            server_policy.update({interaction.guild.id: length})
            await interaction.response.send_message(f"Set the message history of this server to {length} days",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message("I cannot delete messages longer than 14 days, pick a number lower"
                                                    "than 14")
    else:
        # Timeout those who mess with admin settings
        duration = timedelta(minutes=30)
        expiration_time: datetime = discord.utils.utcnow() + duration
        await interaction.user.timeout(expiration_time)


@tree.command(name="remove_disappearing_messages", description="Removes the disappearing messages feature of your "
                                                               "server")
async def remove_history(interaction: discord):
    # Check that the use has the administrator permission to use it
    if interaction.user.guild_permissions.administrator:
        # Check if the server has enabled the disappearing messages feature
        if interaction.guild.id in server_policy:
            # Remove the server id from the dictionary
            server_policy.pop(interaction.guild.id)
            await interaction.response.send_message(f"Removed the message history of this server",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message("This server does not have a message history", ephemeral=True)
    else:
        # Timeout those who mess with admin settings
        duration = timedelta(minutes=30)
        expiration_time: datetime = discord.utils.utcnow() + duration
        await interaction.user.timeout(expiration_time)


# Runs as soon as the code is ready
@client.event
async def on_ready():
    await tree.sync()
    print(f'We have logged in as {client.user}')
    hourly_schedule.start()


client.run(open('token', 'r').read())
