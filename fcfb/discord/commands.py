import sys

from fcfb.discord.game import start_game

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

    messageContent = message.content.lower()

    # Handle start game command
    if messageContent.startswith(prefix + 'start'):
        command = messageContent.split('start')[1].strip()
        try:
            gameParameters = command.split('[')[1].split(']')[0].split(',').strip()
            if len(gameParameters) != 7:
                exceptionMessage = "Error parsing parameters for start game command"
                logger.error(exceptionMessage)
                return e(exceptionMessage)
        except Exception as e:
            exceptionMessage = "Error parsing parameters for start game command"
            logger.error(exceptionMessage)
            return e(exceptionMessage)

        logger.info("Starting game with parameters: " + str(gameParameters))
        await start_game(client, configData, message, gameParameters, logger)

