import re
import sys

from fcfb.api.zebstrika.game_plays import submit_defensive_number, submit_offensive_number
from fcfb.api.zebstrika.games import post_game, get_ongoing_game_by_channel_id, delete_ongoing_game, \
    get_ongoing_game_by_id, update_waiting_on
from fcfb.api.zebstrika.users import get_user_by_team
from fcfb.discord.utils import create_channel, create_message, get_discord_user_by_name, delete_channel, \
    send_direct_message, find_previous_direct_message_embed_and_get_game_id, find_previous_game_channel_embed, \
    get_channel_by_id, create_message_with_embed, craft_number_request_embed

sys.path.append("..")


async def start_game(client, config_data, discord_messages, message, game_parameters, logger):
    """
    Start a game
    :param client:
    :param config_data:
    :param discord_messages:
    :param message:
    :param game_parameters:
    :param logger:
    :return:
    """

    game_channel = None

    try:
        # Validate the number of game parameters
        if len(game_parameters) != 9:
            raise ValueError("Error parsing parameters for starting a game. Expected 7 parameters.")

        # Extract game parameters
        season, week, subdivision, home_team, away_team, tv_channel, start_time, location, is_scrimmage = map(str.strip, game_parameters)

        # Update scrimmage
        if is_scrimmage.lower == "yes":
            is_scrimmage = "true"
        elif is_scrimmage.lower == "no":
            is_scrimmage = "false"
        else:
            raise ValueError("Error parsing scrimmage parameter. Expected **yes** or **no**.")

        # Create game channel
        channel_name = f"{away_team} at {home_team} S{season} W{week} {subdivision}"
        if is_scrimmage == "true":
            channel_name += " (Scrimmage)"
        game_channel = await create_channel(message, channel_name, "Games", logger)

        # Get discord tag of the away coach
        away_coach = await get_user_by_team(config_data, away_team, logger)
        away_coach_tag = away_coach['discordTag']

        # Get discord user object of the away coach
        away_coach_discord_object = await get_discord_user_by_name(client, away_coach_tag, logger)

        # Start the game
        await post_game(config_data, game_channel.id, season, week, subdivision, home_team, away_team, tv_channel, start_time,
                        location, is_scrimmage, logger)

        # Prompt for coin toss
        start_game_message = discord_messages["gameStartMessage"].format(
            away_coach_discord_object=away_coach_discord_object.mention)

        await create_message(game_channel, start_game_message, logger)

    except ValueError as ve:
        error_message = f"Error starting game: {ve}"
        await create_message(message.channel, error_message, logger)
        logger.error(error_message)

        # If an error occurs, delete the game channel if it was created
        if game_channel is not None:
            await delete_game(config_data, game_channel, logger)

    except Exception as e:
        error_message = f"An unexpected error occurred while starting the game:\n{e}"
        await create_message(message.channel, error_message, logger)
        logger.error(error_message)

        # If an error occurs, delete the game channel if it was created
        if game_channel is not None:
            await delete_game(config_data, game_channel, logger)


async def delete_game(config_data, game_channel, logger):
    """
    Delete the game from the database and delete the channel

    :param config_data:
    :param game_channel:
    :param logger:
    :return:
    """

    try:
        game_object = await get_ongoing_game_by_channel_id(config_data, game_channel.id, logger)
        await delete_ongoing_game(config_data, game_object['gameId'], logger)

        if 'game_channel' in locals() and game_channel:
            await delete_channel(game_channel, logger)

    except Exception as e:
        error_message = f"An unexpected error occurred while deleting the game:\n{e}"
        await create_message(game_channel, error_message, logger)
        logger.error(error_message)


async def validate_and_submit_offensive_number(client, config_data, discord_messages, message, logger):
    """
    Validate the offensive number and submit it to the API

    :param client:
    :param config_data:
    :param discord_messages:
    :param message:
    :param logger:
    :return:
    """
    try:
        game_object = await get_ongoing_game_by_channel_id(config_data, message.channel.id, logger)
        game_id = game_object["gameId"]

        home_user_object, away_user_object = await get_user_objects(config_data, game_object, logger)

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
                                                    offensive_timeout_called, defensive_timeout_called, logger)

        # Print the play result
        await create_message(message.channel, play_result, logger)

        # Send the prompt for the next number
        if play_result["possession"] == "home":
            await message_defense_for_number(client, config_data, discord_messages, message, game_object,
                                             play_result["awayTeam"], logger)
        else:
            await message_defense_for_number(client, config_data, discord_messages, message, game_object,
                                             play_result["homeTeam"], logger)

    except ValueError as ve:
        exception_message = str(ve)
        logger.error(exception_message)
        await create_message(message.channel, exception_message, logger)

    except Exception as e:
        exception_message = f"An unexpected error occurred while submitting an offensive number:\n{e}"
        logger.error(exception_message, exc_info=True)
        await create_message(message.channel, exception_message, logger)
        raise Exception(exception_message)


async def validate_and_submit_defensive_number(client, config_data, discord_messages, message, logger):
    """
    Validate the defensive number and submit it to the API

    :param client:
    :param config_data:
    :param discord_messages:
    :param message:
    :param logger:
    :return:
    """
    try:
        game_id, prev_message_content = await find_previous_direct_message_embed_and_get_game_id(client, message)
        game_id = game_id.split("**Game ID: ")[1].split("**")[0].strip() if game_id is not None else None
        validate_game_id(game_id)

        game_object = await get_ongoing_game_by_id(config_data, game_id, logger)
        play_type = game_object["currentPlayType"]

        home_user_object, away_user_object = await get_user_objects(config_data, game_object, logger)

        validate_waiting_on(message, game_object, home_user_object, away_user_object)

        validate_no_possession(message, game_object, home_user_object, away_user_object)

        defensive_number = parse_play_number(message.content)
        validate_play_number(defensive_number)

        username = get_opponent_username(game_object, home_user_object, away_user_object)

        # Look if defense called timeout
        defense_timeout_called = parse_timeout_called(message.content)

        # Submit defensive number and update waiting on
        await submit_defensive_number(config_data, game_id, defensive_number, defense_timeout_called, logger)
        await update_waiting_on(config_data, game_id, username, logger)

        # Send confirmation DM and send the prompt for the offensive number
        if defense_timeout_called:
            await send_direct_message(message.author, f"Your defensive number has been submitted, it is "
                                                      f"{defensive_number}. Defense called timeout.", logger)
        else:
            await send_direct_message(message.author, f"Your defensive number has been submitted, it is "
                                                      f"{defensive_number}.", logger)

        # Send the prompt for the offensive number
        await message_offense_for_number(client, config_data, discord_messages, message, game_object, home_user_object,
                                         away_user_object, play_type, username, defense_timeout_called, logger)

    except ValueError as ve:
        exception_message = str(ve)
        logger.error(exception_message)
        await create_message(message.channel, exception_message, logger)

    except Exception as e:
        exception_message = f"An unexpected error occurred while submitting a defensive number:\n{e}"
        logger.error(exception_message, exc_info=True)
        await create_message(message.channel, exception_message, logger)
        raise Exception(exception_message)


async def message_offense_for_number(client, config_data, discord_messages, message, game_object, home_user_object,
                                     away_user_object, play_type, username, defense_timeout_called, logger):
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
    :param logger:
    :return:
    """

    if username == home_user_object["username"]:
        offensive_coach = home_user_object
    else:
        offensive_coach = away_user_object
    offensive_coach_tag = offensive_coach["discordTag"]

    offensive_coach_discord_object = await get_discord_user_by_name(client, offensive_coach_tag, logger)

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
        raise ValueError("Invalid current play type")

    channel_id = None
    if game_object["homePlatform"] == "Discord":
        channel_id = game_object["homePlatformId"]
    if game_object["awayPlatform"] == "Discord":
        channel_id = game_object["awayPlatformId"]

    if channel_id is None:
        logger.info(f"INFO: Neither user is playing on Discord in game {game_object['gameId']}")
        return

    embed = await craft_number_request_embed(config_data, message, defense_timeout_called, logger, channel_id)
    channel = await get_channel_by_id(client, channel_id, logger)
    await create_message_with_embed(channel, number_request_message, embed, logger)


async def message_defense_for_number(client, config_data, discord_messages, message, game_object, team, logger):
    """
    Message the defense for a number.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param message: Discord message object.
    :param game_object: Game object.
    :param team: Team name.
    :param logger: Logger object.
    :return: None
    """

    try:
        if team == game_object["homeTeam"] and game_object["homePlatform"] != "Discord":
            logger.info("INFO: Home team is not on Discord, not attempting to message")
            return
        if team == game_object["awayTeam"] and game_object["awayPlatform"] != "Discord":
            logger.info("INFO: Away team is not on Discord, not attempting to message")
            return

        coach = await get_user_by_team(config_data, team, logger)
        game_id = game_object["gameId"]
        play_type = game_object["currentPlayType"]

        await update_waiting_on(config_data, game_id, coach["username"], logger)

        embed = await craft_number_request_embed(config_data, message, False, logger)
        coach_tag = coach["discordTag"]
        coach_discord_object = await get_discord_user_by_name(client, coach_tag, logger)

        if play_type == "KICKOFF":
            number_message = discord_messages["kickingNumberDefenseMessage"]
        elif play_type == "NORMAL":
            number_message = discord_messages["normalNumberDefenseMessage"]
        elif play_type == "POINT AFTER":
            number_message = discord_messages["pointAfterDefenseMessage"]
        else:
            ValueError("Invalid current play type")
            return

        await send_direct_message(coach_discord_object, number_message, logger, embed)
        logger.info("SUCCESS: Defense was messaged for a number in channel " + str(message.channel.id))

    except ValueError as ve:
        exception_message = str(ve)
        await create_message(message.channel, exception_message, logger)
    except Exception as e:
        error_message = f"An unexpected error occurred while messaging the defense for a number:\n{e}"
        await create_message(message.channel, error_message, logger)
        logger.error(error_message)
        raise Exception(error_message)


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


async def get_user_objects(config_data, game_object, logger):
    """
    Get the game and user objects from the game id
    :param config_data:
    :param game_object:
    :param logger:
    :return:
    """

    home_user_object = await get_user_by_team(config_data, game_object["homeTeam"], logger)
    away_user_object = await get_user_by_team(config_data, game_object["awayTeam"], logger)

    return home_user_object, away_user_object


def validate_game_id(game_id):
    """
    Validate the game id
    :param game_id:
    :return:
    """

    if game_id is None:
        raise ValueError("Could not find a valid game id in previous messages, are you sure you are in a game?")


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
        raise ValueError(f"I am not waiting on a number from you currently. Currently waiting on a number from "
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
        raise ValueError("You have possession, please submit your number in the game channel instead")


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
        raise ValueError("You don't have possession, please submit your number in your DMs instead. "
                         "The game is waiting on you.")


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
        raise ValueError("I could not find a valid number in your message, please try again")


def validate_play_number(play_number):
    """
    Validate the play number is between 1 and 1500, inclusive

    :param play_number:
    :return:
    """

    if not (1 <= play_number <= 1500):
        raise ValueError("The number you submitted is not between 1 and 1500, please try again")


def parse_normal_play(message_content):
    """
    Parse the normal play type from the message content

    :param message_content:
    :return:
    """

    play_type_match = re.search(r'\b(run|pass|spike|kneel|field goal|punt)\b', message_content, flags=re.IGNORECASE)

    if play_type_match:
        return play_type_match.group().lower()
    else:
        raise ValueError("I could not find a valid play in your message, please select **run**, **pass**, **spike**, "
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
        raise ValueError("I could not find a valid play in your message, please select **normal**, **onside**, "
                         "or **squib** and try again")


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
        raise ValueError("I could not find a valid play in your message, "
                         "please select **two point** or **pat** and try again")


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
