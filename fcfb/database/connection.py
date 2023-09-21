import mariadb


async def connect_to_db(configData, logger):
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
            database=configData['database']['name'],
        )

    except mariadb.Error as e:
        logger.error(f"Error connecting to MariaDB Platform: {e}")
        return None

    return db