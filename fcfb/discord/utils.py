import discord


async def get_discord_user_by_name(client, name, logger):
    """
    Get a discord user by name

    :param client:
    :param id:
    :param logger:
    :return:
    """

    try:
        user = discord.utils.get(client.users, name=name)
        return user
    except Exception as e:
        exceptionMessage = "Error getting Discord user"
        logger.error(exceptionMessage)
        return e(exceptionMessage)


async def create_game_channel(message, homeTeam, awayTeam, logger):
    """
    Create a game channel for a game

    :param homeTeam:
    :param awayTeam:
    :return:
    """

    # Create game channel
    try:
        gameChannel = await message.guild.create_text_channel(awayTeam + " @ " + homeTeam)
        logger.info("Game channel created for " + awayTeam + " @ " + homeTeam)
        return gameChannel
    except Exception as e:
        exceptionMessage = "Error creating game channel"
        logger.error(exceptionMessage)
        return e(exceptionMessage)


async def create_message(channel, messageText, logger):
    """
    Create a message

    :param channel:
    :param messageText:
    :return:
    """

    try:
        await channel.send(messageText)
    except Exception as e:
        exceptionMessage = "Error sending message to channel"
        logger.error(exceptionMessage)
        return e(exceptionMessage)
