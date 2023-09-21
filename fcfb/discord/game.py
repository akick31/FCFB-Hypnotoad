import sys

from fcfb.discord.utils import create_channel, create_message, get_discord_user_by_name
from fcfb.database.communication import retrieve_value_from_table

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
    season = gameParameters[0]
    subdivision = gameParameters[1]
    homeTeam = gameParameters[2]
    awayTeam = gameParameters[3]
    tvChannel = gameParameters[4]
    startTime = gameParameters[5]
    location = gameParameters[6]

    # Create game channel
    try:
        channelName = awayTeam + " at " + homeTeam + " (Season " + season + " | " + subdivision + ")"
        gameChannel = await create_channel(message, channelName, logger)
        awayCoachTag = await retrieve_value_from_table(configData, "users", "name", awayTeam, "discord_tag", logger)
        awayCoachDiscord = await get_discord_user_by_name(client, awayCoachTag, logger)

        # Prompt for coin toss
        await create_message(gameChannel, "Coin toss time! " + awayCoachDiscord.mention + ", you're away, call "
                                          "**heads** or **tails** in the air", logger)
    except Exception as e:
        await create_message(message.channel, "Error starting game: " + str(e), logger)
        return