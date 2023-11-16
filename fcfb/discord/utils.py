import discord


async def get_discord_user_by_name(client, name, logger):
    """
    Get a Discord user by name

    :param client:
    :param name:
    :param logger:
    :return:
    """

    try:
        user = discord.utils.get(client.users, name=name)
        if user is None:
            raise Exception("User not found")
        return user
    except Exception as e:
        error_message = "Error getting Discord user"
        logger.error(error_message)
        raise Exception(error_message)


async def create_channel(message, channel_name, category_name, logger):
    """
    Create a channel

    :param message:
    :param channel_name:
    :param category_name:
    :param logger:
    :return:
    """

    try:
        category = await get_category_by_name(message, category_name, logger)
        game_channel = await message.guild.create_text_channel(channel_name, category=category)
        logger.info("Channel named " + channel_name + " created")
        return game_channel
    except Exception as e:
        error_message = "Error creating channel"
        logger.error(error_message)
        raise Exception(error_message)


async def delete_channel(channel, logger):
    """
    Delete a channel

    :param channel:
    :param logger:
    :return:
    """

    try:
        await channel.delete()
        logger.info("Channel named " + channel.name + " deleted")
    except Exception as e:
        error_message = "Error deleting channel"
        logger.error(error_message)
        raise Exception(error_message)


async def get_category_by_name(message, category_name, logger):
    """
    Get a category by name

    :param message:
    :param category_name:
    :param logger:
    :return:
    """

    try:
        category = discord.utils.get(message.guild.categories, name=category_name)
        if category is None:
            raise Exception("Category not found")
        return category
    except Exception as e:
        error_message = "Error getting category"
        logger.error(error_message)
        raise Exception(error_message)


async def get_channel_by_id(client, config_data, channel_id, logger):
    """
    Get a Discord channel by ID

    :param client: Discord client object
    :param config_data: Config data
    :param channel_id: ID of the channel to retrieve
    :param logger: Logger object
    :return: Channel object or None if not found
    """

    try:
        channel = client.get_channel(int(channel_id))
        if channel is None:
            raise Exception(f"Channel with ID {channel_id} not found")
        return channel
    except Exception as e:
        error_message = f"Error getting Discord channel with ID {channel_id}"
        logger.error(error_message)
        raise Exception(error_message)


async def create_message(channel, message_text, logger):
    """
    Create a message

    :param channel:
    :param message_text:
    :param logger:
    :return:
    """

    try:
        await channel.send(message_text)
    except Exception as e:
        error_message = "Error sending message to channel"
        logger.error(error_message)
        raise Exception(error_message)


async def create_message_with_embed(channel, message_text, embed, logger):
    """
    Create a message with an embed

    :param channel:
    :param message_text:
    :param embed:
    :return:
    """

    try:
        await channel.send(message_text, embed=embed)
    except Exception as e:
        error_message = "Error sending embed message to channel"
        logger.error(error_message)
        raise Exception(error_message)


async def send_direct_message(user, message_text, logger, embed=None):
    """
    Send a direct message to a user

    :param user: Discord user object
    :param message_text: Text of the message to be sent
    :param logger: Logger object
    :param embed: Embed object
    :return:
    """

    try:
        if embed is None:
            await user.send(message_text)
        else:
            await user.send(message_text, embed=embed)
        logger.info(f"Direct message sent to {user.name}")
    except discord.Forbidden:
        # The user has DMs disabled or has blocked the bot
        logger.error(f"Failed to send a direct message to {user.name}. "
                     f"The user may have DMs disabled or blocked the bot.")
    except Exception as e:
        error_message = "Error sending direct message"
        logger.error(error_message)
        raise Exception(error_message)