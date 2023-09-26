import sys

from fcfb.discord.utils import create_channel, create_message, get_discord_user_by_name, delete_channel
from fcfb.database.communication import retrieve_value_from_table, add_row_to_table
from fcfb.api.zebstrika import send_post_request_to_zebstrika

sys.path.append("..")


async def start_game(client, configData, message, gameParameters, logger):
    """
    Start a game
    :param configData:
    :param message:
    :param gameParameters:
    :param logger:
    :return:
    """

    # Get game parameters
    season = gameParameters[0].strip()
    subdivision = gameParameters[1].strip()
    homeTeam = gameParameters[2].strip()
    awayTeam = gameParameters[3].strip()
    tvChannel = gameParameters[4].strip()
    startTime = gameParameters[5].strip()
    location = gameParameters[6].strip()

    # Create game channel
    try:
        # TODO change retrieve value and get discord user to being an api call
        channelName = awayTeam + " at " + homeTeam + " S" + season + " " + subdivision
        gameChannel = await create_channel(message, channelName, "Games", logger)
        awayCoachTag = await retrieve_value_from_table(configData, configData["database"]["main_schema"], "users", "team", awayTeam, "discord_tag", logger)
        awayCoachDiscord = await get_discord_user_by_name(client, awayCoachTag, logger)

        # Start game
        payload = "games/start/" + season + "/" + subdivision + "/" + homeTeam + "/" + awayTeam + "/" + tvChannel + "/" + startTime + "/" + location
        gameInfo = await send_post_request_to_zebstrika(configData, payload, logger)

        # Save game info to Hypnotoad database
        columnNames = "game_id, channel_id"
        values = "'" + gameInfo["gameId"] + "', '" + str(gameChannel.id) + "'"
        await add_row_to_table(configData, configData["database"]["bot_schema"], "discord_games", columnNames, values, logger)

        # Prompt for coin toss
        gameStartMessage = configData['parameters']['game_start_message']
        await create_message(gameChannel, gameStartMessage + "\n\n---------------\n\nNow it is time for the coin toss! "
                             + awayCoachDiscord.mention + ", you're away, call **heads** or **tails** in the air",
                             logger)
    except Exception as e:
        await create_message(message.channel, "Error starting game: " + str(e), logger)
        await delete_channel(gameChannel, logger)
        return