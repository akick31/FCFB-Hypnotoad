import sys
import discord

from fcfb.discord.game import start_game
from fcfb.discord.utils import create_message, create_message_with_embed

sys.path.append("..")


async def parse_commands(client, configData, prefix, message, logger):
    """
    Handle commands from Discord users

    :param configData:
    :param prefix:
    :param message:
    :param logger:
    :return:
    """

    messageContentLower = message.content.lower()
    messageContent = message.content

    if messageContentLower.startswith(prefix + 'help'):
        commandList = "start\n"
        parametersList = "[season, subdivision, home team, away team, tv channel, start time, location]\n"
        exampleList = prefix + "start [9, FBS, Ohio State, Michigan, ABC, 12:00 PM, War Memorial Stadium]\n"

        embed=discord.Embed(
            title="Hypnotoad Commands",
            color=discord.Color.green()
        )
        embed.add_field(name="Command", value=commandList, inline=True)
        embed.add_field(name="Parameters", value=parametersList, inline=True)
        embed.add_field(name="Example", value=exampleList, inline=True)
        await create_message_with_embed(message.channel, embed, logger)

    # Handle start game command
    elif messageContentLower.startswith(prefix + 'start'):
        command = messageContent.split('start')[1].strip()
        try:
            gameParameters = command.split('[')[1].split(']')[0].split(',')
            if len(gameParameters) != 7:
                exceptionMessage = "Error parsing parameters for start game command"
                logger.error(exceptionMessage)
                raise e(exceptionMessage)
        except Exception as e:
            exceptionMessage = "Error parsing parameters for start game command"
            logger.error(exceptionMessage)
            await create_message(message.channel, exceptionMessage, logger)
            raise e(exceptionMessage)

        logger.info("Starting game with parameters: " + str(gameParameters))
        await start_game(client, configData, message, gameParameters, logger)

