import discord

from fcfb.api.zebstrika_games import get_ongoing_game_by_channel_id


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
        error_message = f"Error getting Discord user: {e}"
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
        error_message = f"Error creating channel: {e}"
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
        error_message = f"Error deleting channel: {e}"
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
        error_message = f"Error getting category: {e}"
        logger.error(error_message)
        raise Exception(error_message)


async def get_channel_by_id(client, channel_id, logger):
    """
    Get a Discord channel by ID

    :param client: Discord client object
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
        error_message = f"Error getting Discord channel with ID {channel_id}: {e}"
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
        error_message = f"Error sending message to channel: {e}"
        logger.error(error_message)
        raise Exception(error_message)


async def create_message_with_embed(channel, message_text, embed, logger):
    """
    Create a message with an embed

    :param channel:
    :param message_text:
    :param embed:
    :param logger:
    :return:
    """

    try:
        await channel.send(message_text, embed=embed)
    except Exception as e:
        error_message = f"Error sending embed message to channel: {e}"
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
        error_message = f"Error sending direct message: {e}"
        logger.error(error_message)
        raise Exception(error_message)


async def check_if_channel_is_game_channel(config_data, message, logger):
    """
    Check if the channel is a game channel

    :param config_data:
    :param message:
    :param logger:
    :return:
    """

    try:
        game_object = await get_ongoing_game_by_channel_id(config_data, message.channel.id, logger)
        if game_object is None:
            return False
        return True
    except ValueError:
        exception_message = "Error checking if channel is game channel"
        logger.error(exception_message, exc_info=True)
        await create_message(message.channel, exception_message, logger)
        return None


async def find_previous_game_channel_embed(client, message):
    """
    Find the previous embed from the bot asking the user to submit a number and get the game id from it

    :param client:
    :param message:
    :return:
    """

    async for prev_message in message.channel.history(limit=100):
        if prev_message.author.id == client.user.id and prev_message.id != message.id:
            # Check if the previous bot message has an embed with the specified title
            if prev_message.embeds and prev_message.embeds[0].title == "Submit a Number":
                embed_data = prev_message.embeds[0].to_dict()
                prev_message_content = prev_message.content
                break  # Exit the loop once the desired message is found
    else:
        embed_data = None  # If the loop completes without finding the message, set game_id to None
    return embed_data, prev_message_content


async def find_previous_direct_message_embed_and_get_game_id(client, message):
    """
    Find the previous embed from the bot asking the user to submit a number and get the game id from it

    :param client:
    :param message:
    :return:
    """

    async for prev_message in message.channel.history(limit=100):
        if prev_message.author.id == client.user.id and prev_message.id != message.id:
            # Check if the previous bot message has an embed with the specified title
            if prev_message.embeds and prev_message.embeds[0].title == "Submit a Number":
                embed_data = prev_message.embeds[0].to_dict()
                game_id = embed_data['description'] if 'description' in embed_data else None
                prev_message_content = prev_message.content
                break  # Exit the loop once the desired message is found
    else:
        game_id = None  # If the loop completes without finding the message, set game_id to None
    return game_id, prev_message_content

