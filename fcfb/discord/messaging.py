import sys
import discord

from fcfb.discord.game import start_game, delete_game, validate_and_submit_defensive_number, \
    validate_and_submit_offensive_number
from fcfb.discord.utils import create_message, create_message_with_embed, get_discord_user_by_name, \
    send_direct_message, check_if_channel_is_game_channel, get_channel_by_id
from fcfb.api.zebstrika_games import get_ongoing_game_by_channel_id, run_coin_toss, update_coin_toss_choice, \
    update_waiting_on
from fcfb.api.zebstrika_users import get_user_by_team

sys.path.append("..")


async def parse_commands(client, config_data, discord_messages, prefix, message, logger):
    """
    Handle commands from Discord users.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param prefix: Command prefix.
    :param message: Discord message object.
    :param logger: Logger object.
    :return: None
    """

    message_content_lower = message.content.lower()
    message_content = message.content

    try:
        if message_content_lower.startswith(prefix + 'help'):
            await display_help_command(message.channel, prefix, logger)

        # TODO make sure only admins can do certain commands
        elif message_content_lower.startswith(prefix + 'start'):
            command = message_content.split('start')[1].strip()
            await start_game_command(client, config_data, discord_messages, command, message, logger)

        elif message_content_lower.startswith(prefix + 'delete'):
            await delete_game_command(config_data, message, logger)

        elif message_content_lower.startswith(prefix + 'coin'):
            coin_toss_choice = message_content.split('coin')[1].strip()
            await coin_toss_command(client, config_data, discord_messages, coin_toss_choice, message, logger)

        elif message_content_lower.startswith(prefix + 'choice'):
            coin_toss_choice = message_content.split('choice')[1].strip()
            await coin_toss_choice_command(client, config_data, discord_messages, coin_toss_choice, message, logger)

        elif check_if_channel_is_game_channel(config_data, message, logger):
            await validate_and_submit_defensive_number(client, config_data, discord_messages, message, logger)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise Exception("An unexpected error occurred")


async def parse_direct_message_number_submission(client, config_data, discord_messages, message, logger):
    """
    Handle direct messages from Discord users.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param message: Discord message object.
    :param logger: Logger object.
    :return: None
    """

    await validate_and_submit_defensive_number(client, config_data, discord_messages, message, logger)


async def parse_game_channel_messages(client, config_data, discord_messages, message, logger):
    """
    Handle messages from game channels.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param message: Discord message object.
    :param logger: Logger object.
    :return: None
    """

    await validate_and_submit_offensive_number(client, config_data, discord_messages, message, logger)


async def display_help_command(channel, prefix, logger):
    """
    Display help command with usage information.

    :param channel: Discord channel.
    :param prefix: Command prefix.
    :param logger: Logger object.
    :return: None
    """

    command_list = "start\n"
    parameters_list = "[season, subdivision, home team, away team, tv channel, start time, location]\n"
    example_list = prefix + "start [9, FBS, Ohio State, Michigan, ABC, 12:00 PM, War Memorial Stadium]\n"

    embed = discord.Embed(
        title="Hypnotoad Commands",
        color=discord.Color.green()
    )
    embed.add_field(name="Command", value=command_list, inline=True)
    embed.add_field(name="Parameters", value=parameters_list, inline=True)
    embed.add_field(name="Example", value=example_list, inline=True)
    await create_message_with_embed(channel, "", embed, logger)
    logger.info("SUCCESS: Help command processed")


async def start_game_command(client, config_data, discord_messages, command, message, logger):
    """
    Handle command to start a game.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param command: Command string.
    :param message: Discord message object.
    :param logger: Logger object.
    :return: None
    """

    try:
        game_parameters = command.split('[')[1].split(']')[0].split(',')
        if len(game_parameters) != 7:
            raise ValueError("Error parsing parameters for start game command")

        logger.info("Starting game with parameters: " + str(game_parameters))
        await start_game(client, config_data, discord_messages, message, game_parameters, logger)
        logger.info("SUCCESS: Game started with parameters: " + str(game_parameters) + " in channel: "
                    + str(message.channel.id))

    except ValueError as ve:
        exception_message = str(ve)
        await create_message(message.channel, exception_message, logger)
        raise ValueError(exception_message)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise Exception("An unexpected error occurred")


async def coin_toss_command(client, config_data, discord_messages, coin_toss_call, message, logger):
    """
    Handle command to call a coin toss.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param coin_toss_call: The coin toss call, heads or tails.
    :param message: Discord message object.
    :param logger: Logger object.
    :return: None
    """

    try:
        # Verify game is waiting on coin toss
        game_object = await get_ongoing_game_by_channel_id(config_data, message.channel.id, logger)
        if game_object["coinTossWinner"] is not None and game_object["coinTossWinner"] != "None":
            raise ValueError("Game is not waiting on a coin toss")

        game_id = game_object["gameId"]

        # Get coin toss choice
        if coin_toss_call not in ['heads', 'tails']:
            raise ValueError("Invalid coin toss call, please call **heads** or **tails**")

        logger.info("Coin toss called: " + str(coin_toss_call))

        game_object = await run_coin_toss(config_data, game_id, coin_toss_call, logger)

        coin_toss_winning_coach = await get_user_by_team(config_data, game_object["coinTossWinner"], logger)
        coin_toss_winning_coach_tag = coin_toss_winning_coach['discordTag']

        coin_toss_winning_coach_object = await get_discord_user_by_name(client, coin_toss_winning_coach_tag, logger)

        # Update waiting on
        await update_waiting_on(config_data, game_id, coin_toss_winning_coach["username"], logger)

        # Make Discord comment
        coin_toss_result_message = discord_messages["coinTossResultMessage"].format(
            winner=coin_toss_winning_coach_object.mention)
        await create_message(message.channel, coin_toss_result_message, logger)
        logger.info("SUCCESS: Coin toss was run and won by " + str(coin_toss_winning_coach["username"]) +
                    " in channel " + str(message.channel.id) + " with call " + str(coin_toss_call))

    except ValueError as ve:
        exception_message = str(ve)
        await create_message(message.channel, exception_message, logger)
    except Exception as e:
        error_message = f"An unexpected error occurred while processing the coin toss:\n{e}"
        await create_message(message.channel, error_message, logger)
        logger.error(error_message)
        raise Exception(error_message)


async def coin_toss_choice_command(client, config_data, discord_messages, coin_toss_choice, message, logger):
    """
    Handle command to update a coin toss choice to receive or defer.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param coin_toss_choice: The coin toss choice, receive or defer.
    :param message: Discord message object.
    :param logger: Logger object.
    :return: None
    """

    try:
        # Verify game is waiting on coin toss choice
        game_object = await get_ongoing_game_by_channel_id(config_data, message.channel.id, logger)
        if game_object["coinTossChoice"] == "receive" or game_object["coinTossWinner"] == "defer":
            raise ValueError("Game is not waiting on a coin toss choice at this time")

        game_id = game_object["gameId"]

        # Get coin toss choice as receive or defer
        if coin_toss_choice not in ['receive', 'defer']:
            raise ValueError("Invalid choice, please select **receive** or **defer**")

        logger.info("Coin toss choice selected: " + str(coin_toss_choice))

        game_object = await update_coin_toss_choice(config_data, game_id, coin_toss_choice, logger)

        # Make Discord comment
        coin_toss_choice_message = discord_messages["coinTossChoiceMessage"].format(
            winner=game_object["coinTossWinner"],
            choice=game_object["coinTossChoice"])
        await create_message(message.channel, coin_toss_choice_message, logger)

        # Update the team waiting on
        coin_toss_winner = game_object["coinTossWinner"]
        coin_toss_choice = game_object["coinTossChoice"]

        if coin_toss_winner == game_object["homeTeam"]:
            receiving_team = game_object["awayTeam"] if coin_toss_choice == "defer" else game_object["homeTeam"]
        elif coin_toss_winner == game_object["awayTeam"]:
            receiving_team = game_object["homeTeam"] if coin_toss_choice == "defer" else game_object["awayTeam"]
        else:
            raise ValueError("Invalid coin toss winner")

        await message_defense_for_number(client, config_data, discord_messages, message, game_object, receiving_team,
                                         logger)
        logger.info("SUCCESS: Coin toss choice was updated to " + str(coin_toss_choice) + " in channel "
                    + str(message.channel.id))

    except ValueError as ve:
        exception_message = str(ve)
        await create_message(message.channel, exception_message, logger)
    except Exception as e:
        error_message = f"An unexpected error occurred while processing the coin toss choice:\n{e}"
        await create_message(message.channel, error_message, logger)
        logger.error(error_message)
        raise Exception(error_message)


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

    embed = await craft_number_request_embed(config_data, message, defense_timeout_called, logger,
                                             game_object["platformId"])

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

    channel = await get_channel_by_id(client, game_object["platformId"], logger)
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


async def craft_number_request_embed(config_data, message, defense_called_timeout, logger, channel_id=None):
    """
    Create the embed for number requests

    :param config_data:
    :param message:
    :param defense_called_timeout:
    :param logger:
    :param channel_id:
    :return:
    """

    if channel_id is None:
        game_object = await get_ongoing_game_by_channel_id(config_data, message.channel.id, logger)
    else:
        game_object = await get_ongoing_game_by_channel_id(config_data, channel_id, logger)
    home_score, away_score = int(game_object["homeScore"]), int(game_object["awayScore"])
    down, yards_to_go = game_object["down"], game_object["yardsToGo"]
    ball_location = game_object["ballLocation"]
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
        title="Submit a Number",
        description=f"**Game ID: {game_object['gameId']}**",
        color=discord.Color.green()
    )
    embed.add_field(name="Status", value=status_message, inline=False)
    embed.add_field(name="Instructions", value="Please submit a number between **1** and **1500**, inclusive",
                    inline=False)
    if defense_called_timeout:
        embed.add_field(name="Timeout", value="The defense has called a timeout", inline=False)
    embed.add_field(name="Deadline", value=f"You have until {game_object['gameTimer']} to submit a number",
                    inline=False)

    return embed


async def delete_game_command(config_data, message, logger):
    """
    Handle command to delete a game in the current channel.

    :param config_data: Configuration data.
    :param message: Discord message object.
    :param logger: Logger object.
    :return: None
    """

    try:
        logger.info(f"Deleting game in channel {message.channel.id}")
        await delete_game(config_data, message.channel, logger)
        logger.info(f"SUCCESS: Game deleted in channel {message.channel.id}")

    except ValueError as ve:
        exception_message = str(ve)
        await create_message(message.channel, exception_message, logger)
        raise ValueError(exception_message)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise Exception("An unexpected error occurred")
