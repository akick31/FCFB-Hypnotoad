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
        if user is None:
            raise Exception("User not found")
        return user
    except Exception as e:
        exceptionMessage = "Error getting Discord user"
        logger.error(exceptionMessage)
        raise e(exceptionMessage)


async def create_channel(message, channelName, categoryName, logger):
    """
    Create a channel

    :param channelName
    :return:
    """

    # Create game channel
    try:
        category = await get_category_by_name(message, categoryName, logger)
        gameChannel = await message.guild.create_text_channel(channelName, category=category)
        logger.info("Channel named " + channelName + " created")
        return gameChannel
    except Exception as e:
        exceptionMessage = "Error creating channel"
        logger.error(exceptionMessage)
        raise e(exceptionMessage)


async def delete_channel(channel, logger):
    """
    Delete a channel

    :param message:
    :param channel:
    :param logger:
    :return:
    """

    try:
        await channel.delete()
        logger.info("Channel named " + channel.name + " deleted")
    except Exception as e:
        exceptionMessage = "Error deleting channel"
        logger.error(exceptionMessage)
        raise e(exceptionMessage)


async def get_category_by_name(message, categoryName, logger):
    """
    Get a category by name

    :param message:
    :param categoryName:
    :param logger:
    :return:
    """

    try:
        category = discord.utils.get(message.guild.categories, name=categoryName)
        if category is None:
            raise Exception("Category not found")
        return category
    except Exception as e:
        exceptionMessage = "Error getting category"
        logger.error(exceptionMessage)
        raise e(exceptionMessage)


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
        raise e(exceptionMessage)


async def create_message_with_embed(channel, embed, logger):
    """
    Create a message with an embed

    :param channel:
    :param embed:
    :return:
    """

    try:
        await channel.send(embed=embed)
    except Exception as e:
        exceptionMessage = "Error sending embed message to channel"
        logger.error(exceptionMessage)
        raise e(exceptionMessage)
