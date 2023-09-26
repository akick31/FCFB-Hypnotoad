import mariadb


async def connect_to_db(configData, schema, logger):
    """
    Connect to the database

    :param configData:
    :param schema:
    :param logger:

    :return:
    """

    # Connect to MariaDB Platform
    try:
        db = mariadb.connect(
            user=configData['database']['user'],
            password=configData['database']['password'],
            host=configData['database']['host'],
            port=int(configData['database']['port']),
            database=schema,
        )
        return db

    except mariadb.Error as e:
        exceptionMessage = "Error connecting to the MariaDB Platform: " + str(e)
        logger.error(exceptionMessage)
        raise Exception(exceptionMessage)


async def connect_to_discord_db(configData, logger):
    """
    Connect to the database

    :return:
    """

    # Connect to MariaDB Platform
    try:
        db = mariadb.connect(
            user=configData['database']['user'],
            password=configData['database']['password'],
            host=configData['database']['host'],
            port=int(configData['database']['port']),
            database=configData['parameters']['bot_name'],
        )
        return db

    except mariadb.Error as e:
        exceptionMessage = "Error connecting to the MariaDB Platform: " + str(e)
        logger.error(exceptionMessage)
        raise Exception(exceptionMessage)