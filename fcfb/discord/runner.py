import discord
import sys

sys.path.append("..")

from fcfb.discord.commands import parse_commands

def run_hypnotoad(configData, logger):
    """
    Run Hypnotoad

    :param configData:
    :param logger:
    :return:
    """

    token = configData['discord']['token']
    prefix = configData['parameters']['prefix']

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_message(message):
        if message.content.startswith(prefix):
            await parse_commands(client, configData, prefix, message, logger)

    @client.event
    async def on_ready():
        print('------')
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)
        print('------')

    client.run(token)