import discord
import sys
import logging

from fcfb.api.zebstrika.games import get_ongoing_game_by_thread_id
from fcfb.main.exceptions import async_exception_handler, DiscordAPIError

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


@async_exception_handler()
async def get_discord_user_by_name(client, name):
    """
    Get a Discord user by name

    :param client:
    :param name:
    :return:
    """

    try:
        user = discord.utils.get(client.users, name=name)
        if user is None:
            raise DiscordAPIError("User not found")
        return user
    except Exception as e:
        raise DiscordAPIError(f"There was an issue getting the Discord user object, {e}")


@async_exception_handler()
async def create_game_thread(client, channel_id, home_team, away_team, season, subdivision, week, is_scrimmage):
    """
    Create a thread

    :param client:
    :param channel_id:
    :param home_team:
    :param away_team:
    :param season:
    :param subdivision:
    :param week:
    :param is_scrimmage:
    :return:
    """

    try:
        thread_name = f'{away_team} at {home_team}'
        game_channel = await get_channel_by_id(client, channel_id)
        season_tag = f'Season {season}'
        week_tag = f'Week {week}'
        scrimmage_tag = 'Scrimmage' if is_scrimmage == 'true' else ''
        subdivision_tag = subdivision
        tags = [season_tag, week_tag, scrimmage_tag, subdivision_tag]
        tags_to_apply = await verify_tags_exist(game_channel, tags)

        game_thread = await game_channel.create_thread(
            name=thread_name,
            content="",
            applied_tags=tags_to_apply)
        logger.info("Thread named " + thread_name + " created")
        return game_thread
    except DiscordAPIError as dae:
        raise dae
    except Exception as e:
        raise DiscordAPIError(f"There was an issue creating the thread, {e}")


@async_exception_handler()
async def verify_tags_exist(channel, tags):
    """
    Verify tags exist and create if they do not

    Return the list of tags to apply to the thread

    :param channel:
    :param tags:
    :return:
    """

    try:
        # Get the current tag list
        available_tags = channel.available_tags
        available_tag_names = []
        for tag in available_tags:
            available_tag_names.append(tag.name)

        # Create any tags that do not exist
        for tag in tags:
            if tag not in available_tag_names:
                await create_tag(channel, tag)

        # Get the update tag list
        available_tags = channel.available_tags
        available_tag_names = []
        for tag in available_tags:
            available_tag_names.append(tag.name)

        # Create the list of tags to apply to the thread
        tags_to_apply = []
        for tag in available_tags:
            if tag.name in tags:
                tags_to_apply.append(tag)
        return tags_to_apply
    except DiscordAPIError as dae:
        raise dae
    except Exception as e:
        raise DiscordAPIError(f"There was an issue verifying the tags exist, {e}")


@async_exception_handler()
async def create_tag(channel, tag):
    """
    Create a tag

    :param channel:
    :param tag:
    :return:
    """

    try:
        await channel.create_tag(name=tag)
        logger.info(f"Tag named {tag} created")
    except Exception as e:
        raise DiscordAPIError(f"There was an issue creating the tag, {e}")


@async_exception_handler()
async def delete_thread(thread):
    """
    Delete a thread

    :param thread:
    :return:
    """

    try:
        await thread.delete()
        logger.info("Thread named " + thread.name + " deleted")
    except Exception as e:
        raise DiscordAPIError(f"There was an issue deleting the thread, {e}")


@async_exception_handler()
async def get_category_by_name(message, category_name):
    """
    Get a category by name

    :param message:
    :param category_name:
    :return:
    """

    try:
        category = discord.utils.get(message.guild.categories, name=category_name)
        if category is None:
            raise DiscordAPIError("Category not found")
        return category
    except Exception as e:
        raise DiscordAPIError(f"There was an issue getting the category, {e}")


async def get_channel_by_id(client, channel_id):
    """
    Get a Discord channel by ID

    :param client: Discord client object
    :param channel_id: ID of the channel to retrieve
    :return: Channel object or None if not found
    """

    try:
        thread = client.get_channel(int(channel_id))
        if thread is None:
            raise DiscordAPIError(f"Channel with ID {channel_id} not found")
        return thread
    except Exception as e:
        raise DiscordAPIError(f"There was an issue getting the channel by its ID, {e}")


@async_exception_handler()
async def get_thread_by_id(client, thread_id):
    """
    Get a Discord thread by ID

    :param client: Discord client object
    :param thread_id: ID of the thread to retrieve
    :return: Channel object or None if not found
    """

    try:
        thread = await client.fetch_channel(int(thread_id))
        if thread is None:
            raise DiscordAPIError(f"Thread with ID {thread_id} not found")
        return thread
    except Exception as e:
        raise DiscordAPIError(f"There was an issue getting the thread by its ID, {e}")


@async_exception_handler()
async def create_message(channel, message_text):
    """
    Create a message

    :param channel:
    :param message_text:
    :return:
    """

    try:
        await channel.send(message_text)
    except Exception as e:
        raise DiscordAPIError(f"There was an issue sending a message to the channel, {e}")


@async_exception_handler()
async def create_message_with_embed(channel, message_text, embed):
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
        raise DiscordAPIError(f"There was an issue sending the embed message to the channel, {e}")


@async_exception_handler()
async def send_direct_message(user, message_text, embed=None):
    """
    Send a direct message to a user

    :param user: Discord user object
    :param message_text: Text of the message to be sent
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
        raise DiscordAPIError(f"Failed to send a direct message to {user.name}. "
                              f"The user may have DMs disabled or blocked the bot.")
    except Exception as e:
        raise DiscordAPIError(f"There was an issue sending a direct message, {e}")


@async_exception_handler()
async def craft_embed(game_object):
    """
    Create the embed

    :param game_object
    :return:
    """

    home_score, away_score = int(game_object["homeScore"]), int(game_object["awayScore"])
    down, yards_to_go = int(game_object["down"]), int(game_object["yardsToGo"])
    ball_location = int(game_object["ballLocation"])
    possession, home_team, away_team = game_object["possession"], game_object["homeTeam"], game_object["awayTeam"]

    score_text = (f"{home_team} leads {away_team} {home_score}-{away_score}" if home_score > away_score else
                  f"{away_team} leads {home_team} {home_score}-{away_score}" if home_score < away_score else
                  f"{home_team} and {away_team} are tied {home_score}-{away_score}")

    down_and_distance = f"{down}{'st' if down == 1 else 'nd' if down == 2 else 'rd' if down == 3 else 'th'} and " \
                        f"{yards_to_go}"

    yard_line = (f"{away_team} {100 - ball_location}" if ball_location > 50 and possession == home_team else
                 f"{home_team} {100 - ball_location}" if ball_location > 50 and possession == away_team else
                 f"{home_team} {ball_location}" if possession == home_team else
                 f"{away_team} {ball_location}")

    status_message = f"{score_text}\nQ{game_object['quarter']} | {game_object['clock']} | {down_and_distance} " \
                     f"| :football: {yard_line}"

    embed = discord.Embed(
        title=f"{away_team} at {home_team}",
        description=f"**Game ID: {game_object['gameId']}**",
        color=discord.Color.green()
    )
    embed.add_field(name="Status", value=status_message, inline=False)
    embed.add_field(name="Deadline", value=f"{game_object['waitingOn']} has until {game_object['gameTimer']} to submit a number",
                    inline=False)

    return embed


@async_exception_handler()
async def check_if_location_is_game_thread(config_data, message):
    """
    Check if the location is a game thread

    :param config_data:
    :param message:
    :return:
    """

    try:
        # Cut down on API calls by only looking in channels in the games thread
        if isinstance(message.channel, discord.Thread):
            channel_name = message.channel.parent.name
            if channel_name != "games":
                return False
        else:
            return False

        game_object = await get_ongoing_game_by_thread_id(config_data, message.channel.id)
        if game_object is None:
            return False
        return True
    except Exception as e:
        raise DiscordAPIError(f"There was an issue checking the location is a game thread, {e}")


@async_exception_handler()
async def find_previous_game_channel_prompt(client, message):
    """
    Find the previous message from the bot asking the user to submit a number and get the game id from it

    :param client:
    :param message:
    :return:
    """

    prev_message_content = ""
    async for prev_message in message.channel.history(limit=100):
        if prev_message.author.id == client.user.id and prev_message.id != message.id:
            # Check if the previous bot message has an embed with the specified title
            if "has submitted their defensive number" in prev_message.content:
                prev_message_content = prev_message.content
                break  # Exit the loop once the desired message is found
    return prev_message_content


@async_exception_handler()
async def find_previous_direct_message_embed_and_get_game_id(client, message):
    """
    Find the previous embed from the bot asking the user to submit a number and get the game id from it

    :param client:
    :param message:
    :return:
    """

    prev_message_content = ""
    async for prev_message in message.channel.history(limit=100):
        if prev_message.author.id == client.user.id and prev_message.id != message.id:
            # Check if the previous bot message has an embed with the specified title
            if prev_message.embeds:
                embed_data = prev_message.embeds[0].to_dict()
                game_id = embed_data['description'] if 'description' in embed_data else None
                prev_message_content = prev_message.content
                break  # Exit the loop once the desired message is found
    else:
        game_id = None  # If the loop completes without finding the message, set game_id to None
    return game_id, prev_message_content

