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


async def create_channel(message, channelName, logger):
    """
    Create a channel

    :param channelName
    :return:
    """

    # Create game channel
    try:
        gameChannel = await message.guild.create_text_channel(channelName)
        logger.info("Channel named " + channelName + " created")
        return gameChannel
    except Exception as e:
        exceptionMessage = "Error creating channel"
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
