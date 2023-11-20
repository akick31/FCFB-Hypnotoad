import discord
import sys

from fcfb.discord.commands import parse_commands, parse_direct_message_number_submission
from fcfb.discord.game import validate_and_submit_offensive_number
from fcfb.discord.utils import check_if_channel_is_game_channel

sys.path.append("..")


def run_hypnotoad(config_data, discord_messages, logger):
    """
    Run Hypnotoad

    :param config_data:
    :param discord_messages:
    :param logger:
    :return:
    """

    token = config_data['discord']['token']
    prefix = config_data['parameters']['prefix']

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.guilds = True
    intents.presences = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_message(message):
        if message.author.bot:
            return

        if message.content.startswith(prefix):
            await parse_commands(client, config_data, discord_messages, prefix, message, logger)
        elif isinstance(message.channel, discord.DMChannel):
            await parse_direct_message_number_submission(client, config_data, discord_messages, message, logger)
        elif check_if_channel_is_game_channel(config_data, message, logger):
            await validate_and_submit_offensive_number(client, config_data, discord_messages, message, logger)

    @client.event
    async def on_ready():
        print('------')
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)
        print('------')

    client.run(token)
