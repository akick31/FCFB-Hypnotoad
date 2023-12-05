import discord
import sys
import logging

from fcfb.main.exceptions import async_exception_handler
from fcfb.discord.commands import parse_game_thread_commands, parse_commands, parse_direct_message_number_submission
from fcfb.discord.utils import check_if_location_is_game_thread

sys.path.append("..")

# Set up logging
logging.basicConfig(format='[%(asctime)s] [%(levelname)s] - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger("hypnotoad_logger")

# Add Handlers
stream_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s')
stream_handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(stream_handler)


def run_hypnotoad(config_data, discord_messages):
    """
    Run Hypnotoad

    :param config_data:
    :param discord_messages:
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
    @async_exception_handler()
    async def on_message(message):
        if message.author.bot:
            return

        if message.content.startswith(prefix):
            await parse_commands(client, config_data, discord_messages, prefix, message)
        elif isinstance(message.channel, discord.DMChannel):
            await parse_direct_message_number_submission(client, config_data, discord_messages, message)

        elif await check_if_location_is_game_thread(config_data, message):
            await parse_game_thread_commands(client, config_data, discord_messages, message)

    @client.event
    @async_exception_handler()
    async def on_ready():
        logger.info('------')
        logger.info('Logged in as')
        logger.info(client.user.name)
        logger.info(client.user.id)
        logger.info('------')

    client.run(token)
