import discord

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')


client.run("MTEwMTY1ODkzMzk0MjMwNDgwMA.Gm06Xc.5CzIEfb7T672Zn6BIfPvDlr5-akHFIwnXqwyNc")
