import asyncio
import os
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import tasks

# Define normal Discord stuff
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)

media_queue = []

# Downloads folder regulation
if not os.path.exists("downloads"):
    os.mkdir("downloads")
else:
    # Clear the downloads folder
    for file in os.listdir("downloads"):
        os.remove(f"downloads/{file}")

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
        if length < 14:
            # Add the server id to dictionary and set the message_history alongside it
            server_policy.update({interaction.guild.id: length})
            await interaction.response.send_message(f"Set the message history of this server to {length} days",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message("I cannot delete messages longer than 14 days, pick a number lower"
                                                    " than 14", ephemeral=True)
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


# A command that allows people to download videos from YouTube using yt-dlp
# Flowchart: Queue task -> Download video -> Upload video -> Delete video
@tree.command(name="download-video", description="Downloads a video from YouTube")
async def download(interaction: discord, url: str):
    if interaction.user.id in media_queue:
        await interaction.response.send_message("You have already queued media, please wait for it to finish",
                                                ephemeral=True)
    # Check that the user hasn't queued a video already
    else:
        # Add the user to the queue
        media_queue.append(interaction.user.id)
        # Send a message to the user that their video has been queued
        await interaction.response.send_message("Your video has been queued, hold tight!",
                                                ephemeral=False)
        # Save the video name to be deleted later
        video_name = str(interaction.user.id) + ".mp4"
        # Download the video that satisfies the 25MB limit and is in mp4 format
        process = await asyncio.create_subprocess_shell(
            f'cd downloads && yt-dlp -f "best[filesize<25M]" {url} -o {video_name}')
        # Wait for the video to download
        await process.wait()
        # Upload the file
        await interaction.channel.send(file=discord.File(f"downloads/{video_name}"))
        # Delete the video
        os.remove(f"downloads/{video_name}")
        # Remove the user from the queue
        media_queue.remove(interaction.user.id)


# A command that allows people to download music from YouTube using yt-dlp (use -x for extract audio function)
# Flowchart: Queue task -> Download video -> Upload video -> Delete video
@tree.command(name="download-music", description="Download music anywhere")
async def download_music(interaction: discord, url: str):
    if interaction.user.id in media_queue:
        await interaction.response.send_message("You have already queued media, please wait for it to finish",
                                                ephemeral=True)
    # Check that the user hasn't queued a video already
    else:
        # Add the user to the queue
        media_queue.append(interaction.user.id)
        # Send a message to the user that their video has been queued
        await interaction.response.send_message("Your music has been queued, hold tight!",
                                                ephemeral=False)
        # Save the music name to be deleted later
        music_name = str(interaction.user.id) + ".mp3"
        # Download music that satisfies the 25MB limit
        process = await asyncio.create_subprocess_shell(
            f'cd downloads && yt-dlp -f "best[filesize<25M]" -x --audio-format mp3 {url} -o {music_name}')
        # Wait for the music to download
        await process.wait()
        # Upload the music
        await interaction.channel.send(file=discord.File(f"downloads/{music_name}"))
        # Delete the music
        os.remove(f"downloads/{music_name}")
        # Remove the user from the queue
        media_queue.remove(interaction.user.id)


# Runs as soon as the code is ready
@client.event
async def on_ready():
    await tree.sync()
    print(f'We have logged in as {client.user}')
    hourly_schedule.start()


client.run(open('token', 'r').read())
