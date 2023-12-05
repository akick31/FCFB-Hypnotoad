import re
import sys
import logging

from fcfb.main.exceptions import async_exception_handler, InvalidParameterError
from fcfb.api.zebstrika.game_plays import submit_defensive_number, submit_offensive_number
from fcfb.api.zebstrika.games import post_game, get_ongoing_game_by_thread_id, delete_ongoing_game, \
    get_ongoing_game_by_id, update_waiting_on
from fcfb.api.zebstrika.users import get_user_by_team
from fcfb.discord.utils import create_game_thread, create_message, get_discord_user_by_name, delete_thread, \
    send_direct_message, find_previous_direct_message_embed_and_get_game_id, find_previous_game_channel_embed, \
    get_thread_by_id, create_message_with_embed, craft_number_request_embed
from fcfb.main.exceptions import GameError, DiscordAPIError

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


@async_exception_handler()
async def start_game(client, config_data, discord_messages, game_parameters):
    """
    Start a game
    :param client:
    :param config_data:
    :param discord_messages:
    :param game_parameters:
    :return:
    """

    game_thread = None

    try:
        # Validate the number of game parameters
        if len(game_parameters) != 9:
            raise InvalidParameterError(f"Expected 9 parameters but was {len(game_parameters)}.")

        # Extract game parameters
        season, week, subdivision, home_team, away_team, tv_channel, start_time, location, is_scrimmage = map(str.strip,
                                                                                                              game_parameters)
        # Update scrimmage
        if is_scrimmage.lower() == 'yes':
            is_scrimmage = 'true'
        elif is_scrimmage.lower() == 'no':
            is_scrimmage = 'false'
        else:
            raise InvalidParameterError("Expected **yes** or **no** for scrimmage parameter.")

        # Create game thread
        game_thread = await create_game_thread(client, config_data["discord"]["game_channel_id"], home_team, away_team,
                                               season, subdivision, week, is_scrimmage)

        # Get discord tag of the away coach
        away_coach = await get_user_by_team(config_data, away_team)
        away_coach_tag = away_coach['discordTag']

        # Get discord user object of the away coach
        away_coach_discord_object = await get_discord_user_by_name(client, away_coach_tag)

        # Start the game
        await post_game(config_data, game_thread.id, season, week, subdivision, home_team, away_team, tv_channel,
                        start_time, location, is_scrimmage)

        # Prompt for coin toss
        start_game_message = discord_messages["gameStartMessage"].format(
            away_coach_discord_object=away_coach_discord_object.mention)

        await create_message(game_thread, start_game_message)

    except Exception as e:
        # If an error occurs, delete the game channel if it was created
        if game_thread is not None:
            await delete_game(config_data, game_thread)
        raise Exception(e)


@async_exception_handler()
async def delete_game(config_data, game_thread):
    """
    Delete the game from the database and delete the channel

    :param config_data:
    :param game_thread:
    :return:
    """

    try:
        game_object = await get_ongoing_game_by_thread_id(config_data, game_thread.id)
        await delete_ongoing_game(config_data, game_object['gameId'])

        if 'game_channel' in locals() and game_thread:
            await delete_thread(game_thread)

    except Exception as e:
        raise Exception(e)


@async_exception_handler()
async def validate_and_submit_offensive_number(client, config_data, discord_messages, message):
    """
    Validate the offensive number and submit it to the API

    :param client:
    :param config_data:
    :param discord_messages:
    :param message:
    :return:
    """
    try:
        game_object = await get_ongoing_game_by_thread_id(config_data, message.channel.id)
        game_id = game_object["gameId"]

        home_user_object, away_user_object = await get_user_objects(config_data, game_object)

        validate_waiting_on(message, game_object, home_user_object, away_user_object)

        validate_possession(message, game_object, home_user_object, away_user_object)

        # Get the play number
        offensive_number = parse_play_number(message.content)
        validate_play_number(offensive_number)

        # Get the play type and play id
        play_type = game_object["currentPlayType"]
        play_id = game_object["currentPlayId"]

        # Parse the play
        if play_type == "NORMAL":
            play = parse_normal_play(message.content)
        elif play_type == "KICKOFF":
            play = parse_kickoff_play(message.content)
            play = "kickoff " + play  # Add kickoff to the play, as it is what the API expects
        elif play_type == "POINT AFTER":
            play = parse_point_after_play(message.content)
        else:
            return

        # Get the runoff type
        runoff_type = parse_runoff_type(message.content)

        # Get the offensive timeout called
        offensive_timeout_called = parse_timeout_called(message.content)

        # Get the defensive timeout called
        defensive_timeout_called = await parse_defensive_timeout_called(client, message)

        # If defensive timeout called, set offensive timeout to false
        if defensive_timeout_called:
            offensive_timeout_called = False

        # Submit offensive number and get the play result
        play_result = await submit_offensive_number(config_data, game_id, play_id, offensive_number, play, runoff_type,
                                                    offensive_timeout_called, defensive_timeout_called)

        # Print the play result
        await create_message(message.channel, play_result)

        # Send the prompt for the next number
        if play_result["possession"] == "home":
            await message_defense_for_number(client, config_data, discord_messages, message, game_object,
                                             play_result["awayTeam"])
        else:
            await message_defense_for_number(client, config_data, discord_messages, message, game_object,
                                             play_result["homeTeam"])
    except Exception as e:
        raise Exception(e)


@async_exception_handler()
async def validate_and_submit_defensive_number(client, config_data, discord_messages, message):
    """
    Validate the defensive number and submit it to the API

    :param client:
    :param config_data:
    :param discord_messages:
    :param message:
    :return:
    """
    try:
        game_id, prev_message_content = await find_previous_direct_message_embed_and_get_game_id(client, message)
        game_id = game_id.split("**Game ID: ")[1].split("**")[0].strip() if game_id is not None else None
        validate_game_id(game_id)

        game_object = await get_ongoing_game_by_id(config_data, game_id)
        play_type = game_object["currentPlayType"]

        home_user_object, away_user_object = await get_user_objects(config_data, game_object)

        validate_waiting_on(message, game_object, home_user_object, away_user_object)

        validate_no_possession(message, game_object, home_user_object, away_user_object)

        defensive_number = parse_play_number(message.content)
        validate_play_number(defensive_number)

        username = get_opponent_username(game_object, home_user_object, away_user_object)

        # Look if defense called timeout
        defense_timeout_called = parse_timeout_called(message.content)

        # Submit defensive number and update waiting on
        await submit_defensive_number(config_data, game_id, defensive_number, defense_timeout_called)
        await update_waiting_on(config_data, game_id, username)

        # Send confirmation DM and send the prompt for the offensive number
        if defense_timeout_called:
            await send_direct_message(message.author, f"Your defensive number has been submitted, it is "
                                                      f"{defensive_number}. Defense called timeout.")
        else:
            await send_direct_message(message.author, f"Your defensive number has been submitted, it is "
                                                      f"{defensive_number}.")

        # Send the prompt for the offensive number
        await message_offense_for_number(client, config_data, discord_messages, message, game_object, home_user_object,
                                         away_user_object, play_type, username, defense_timeout_called)

    except Exception as e:
        raise Exception(e)


@async_exception_handler()
async def message_offense_for_number(client, config_data, discord_messages, message, game_object, home_user_object,
                                     away_user_object, play_type, username, defense_timeout_called):
    """
    Message the offense for a number.

    :param client:
    :param config_data:
    :param discord_messages:
    :param message:
    :param game_object:
    :param home_user_object:
    :param away_user_object:
    :param play_type:
    :param username:
    :param defense_timeout_called:
    :return:
    """

    try:
        if username == home_user_object["username"]:
            offensive_coach = home_user_object
        else:
            offensive_coach = away_user_object
        offensive_coach_tag = offensive_coach["discordTag"]

        offensive_coach_discord_object = await get_discord_user_by_name(client, offensive_coach_tag)

        if play_type == "KICKOFF":
            number_request_message = discord_messages["kickingNumberOffenseMessage"].format(
                message_author=message.author.mention,
                offensive_coach_discord_object=offensive_coach_discord_object.mention)
        elif play_type == "NORMAL":
            number_request_message = discord_messages["normalNumberOffenseMessage"].format(
                message_author=message.author.mention,
                offensive_coach_discord_object=offensive_coach_discord_object.mention)
        elif play_type == "POINT AFTER":
            number_request_message = discord_messages["pointAfterOffenseMessage"].format(
                message_author=message.author.mention,
                offensive_coach_discord_object=offensive_coach_discord_object.mention)
        else:
            raise GameError("Invalid current play type")

        thread_id = None
        if game_object["homePlatform"] == "Discord":
            thread_id = game_object["homePlatformId"]
        if game_object["awayPlatform"] == "Discord":
            thread_id = game_object["awayPlatformId"]

        if thread_id is None:
            logger.info(f"INFO: Neither user is playing on Discord in game {game_object['gameId']}")
            return

        embed = await craft_number_request_embed(config_data, message, defense_timeout_called, thread_id)
        thread = await get_thread_by_id(message, thread_id)
        await create_message_with_embed(thread, number_request_message, embed)
    except Exception as e:
        raise Exception(e)


@async_exception_handler()
async def message_defense_for_number(client, config_data, discord_messages, message, game_object, team):
    """
    Message the defense for a number.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param message: Discord message object.
    :param game_object: Game object.
    :param team: Team name.
    :return: None
    """

    try:
        if team == game_object["homeTeam"] and game_object["homePlatform"] != "Discord":
            logger.info("INFO: Home team is not on Discord, not attempting to message")
            return
        if team == game_object["awayTeam"] and game_object["awayPlatform"] != "Discord":
            logger.info("INFO: Away team is not on Discord, not attempting to message")
            return

        coach = await get_user_by_team(config_data, team)
        game_id = game_object["gameId"]
        play_type = game_object["currentPlayType"]

        await update_waiting_on(config_data, game_id, coach["username"])

        embed = await craft_number_request_embed(config_data, message, False)
        coach_tag = coach["discordTag"]
        coach_discord_object = await get_discord_user_by_name(client, coach_tag)

        if play_type == "KICKOFF":
            number_message = discord_messages["kickingNumberDefenseMessage"]
        elif play_type == "NORMAL":
            number_message = discord_messages["normalNumberDefenseMessage"]
        elif play_type == "POINT AFTER":
            number_message = discord_messages["pointAfterDefenseMessage"]
        else:
            raise GameError("Invalid current play type")

        await send_direct_message(coach_discord_object, number_message, embed)
        logger.info("SUCCESS: Defense was messaged for a number in channel " + str(message.channel.id))

    except Exception as e:
        raise Exception(e)


def get_opponent_username(game_object, home_user_object, away_user_object):
    """
    Get the username of the opponent of the user who submitted the number

    :param game_object:
    :param home_user_object:
    :param away_user_object:
    :return:
    """

    return away_user_object["username"] if game_object["waitingOn"] == home_user_object["username"] \
        else home_user_object["username"]


@async_exception_handler()
async def get_user_objects(config_data, game_object):
    """
    Get the game and user objects from the game id
    :param config_data:
    :param game_object:
    :return:
    """

    home_user_object = await get_user_by_team(config_data, game_object["homeTeam"])
    away_user_object = await get_user_by_team(config_data, game_object["awayTeam"])

    return home_user_object, away_user_object


def validate_game_id(game_id):
    """
    Validate the game id
    :param game_id:
    :return:
    """

    if game_id is None:
        raise GameError("Could not find a valid game id in previous messages, are you sure you are in a game?")


def validate_waiting_on(message, game_object, home_user_object, away_user_object):
    """
    Validate the user is waiting on a number from them

    :param message:
    :param game_object:
    :param home_user_object:
    :param away_user_object:
    :return:
    """
    waiting_on_username = game_object["waitingOn"]
    user_object = home_user_object if waiting_on_username == home_user_object["username"] else away_user_object

    if user_object["discordTag"] != message.author.name:
        raise GameError(f"I am not waiting on a number from you currently. Currently waiting on a number from "
                        f"{waiting_on_username}")


def validate_no_possession(message, game_object, home_user_object, away_user_object):
    """
    Validate the user does not have possession of the ball
    :param message:
    :param game_object:
    :param home_user_object:
    :param away_user_object:
    :return:
    """

    possession, author_name = game_object["possession"], message.author.name

    if (possession == "home" and home_user_object["discordTag"] == author_name) \
            or (possession == "away" and away_user_object["discordTag"] == author_name):
        raise GameError("You have possession, please submit your number in the game channel instead")


def validate_possession(message, game_object, home_user_object, away_user_object):
    """
    Validate the user has possession of the ball

    :param message:
    :param game_object:
    :param home_user_object:
    :param away_user_object:
    :return:
    """

    possession, author_name = game_object["possession"], message.author.name

    if (possession == "home" and away_user_object["discordTag"] == author_name) \
            or (possession == "away" and home_user_object["discordTag"] == author_name):
        raise GameError("The game is waiting on the user, but they don't have possession, "
                        "submit the number in DMs instead.")


def parse_play_number(message_content):
    """
    Parse the play number from the message content

    :param message_content:
    :return:
    """

    play_number = re.search(r'\b\d+\b', message_content)

    if play_number:
        return int(play_number.group())
    else:
        raise GameError("I could not find a valid number in the message")


def validate_play_number(play_number):
    """
    Validate the play number is between 1 and 1500, inclusive

    :param play_number:
    :return:
    """

    if not (1 <= play_number <= 1500):
        raise GameError("The number submitted is not between 1 and 1500")


def parse_normal_play(message_content):
    """
    Parse the normal play type from the message content

    :param message_content:
    :return:
    """

    play_type_match = re.search(r'\b(run|raise Exception(e)|spike|kneel|field goal|punt)\b', message_content, flags=re.IGNORECASE)

    if play_type_match:
        return play_type_match.group().lower()
    else:
        raise GameError("There was not a valid play in the message, please select **run**, **raise Exception(e)**, **spike**, "
                        "**kneel**, **field goal**, or **punt** and try again")


def parse_kickoff_play(message_content):
    """
    Parse the kickoff play type from the message content

    :param message_content:
    :return:
    """

    play_type_match = re.search(r'\b(normal|onside|squib)\b', message_content, flags=re.IGNORECASE)

    if play_type_match:
        return play_type_match.group().lower()
    else:
        raise GameError("There was not a valid play in the message, options are **normal**, **onside**, or **squib**")


def parse_point_after_play(message_content):
    """
    Parse the point after play type from the message content

    :param message_content:
    :return:
    """

    play_type_match = re.search(r'\b(two point|pat)\b', message_content, flags=re.IGNORECASE)

    if play_type_match:
        return play_type_match.group().lower()
    else:
        raise GameError("There was not a valid play in the message, options are **two point** or **pat**")


def parse_runoff_type(message_content):
    """
    Parse the runoff type from the message content

    :param message_content:
    :return:
    """

    runoff_match = re.search(r'\b(chew|hurry)\b', message_content, flags=re.IGNORECASE)

    if runoff_match:
        return runoff_match.group().lower()
    else:
        return "normal"


def parse_timeout_called(message_content):
    """
    Parse the timeout called from the message content

    :param message_content:
    :return:
    """

    timeout_match = re.search(r'\b(timeout)\b', message_content, flags=re.IGNORECASE)

    if timeout_match:
        return True
    else:
        return False


async def parse_defensive_timeout_called(client, message):
    """
    Parse if defense timeout called from the previous message embed

    :param client:
    :param message:
    :return:
    """

    embed_data, prev_message_content = await find_previous_game_channel_embed(client, message)

    if "Timeout" in embed_data:
        return True
    else:
        return False
