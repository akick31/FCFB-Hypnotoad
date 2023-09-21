import logging

from fcfb.database.connection import connect_to_db


async def retrieve_row_from_table(configData, tableName, whereColumn, whereValue, logger):
    """
    Retrieve a row in a table

    :param configData:
    :param tableName:
    :param whereColumn:
    :param whereValue:
    :param logger:
    :return:
    """

    # Connect to the database
    db = await connect_to_db(configData)
    if db is None:
        exceptionMessage = "Error connecting to the database, please try again later"
        logger.error(exceptionMessage)
        return Exception(exceptionMessage)

    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM " + tableName +
                       " WHERE UPPER(" + whereColumn + ") LIKE UPPER('" + whereValue + "')")
        row = cursor.fetchall()
        db.close()
        return row
    except Exception as e:
        exceptionMessage = "Error retrieving row from database table " + tableName + ": " + str(e)
        logger.error(exceptionMessage)
        db.close()
        return e(exceptionMessage)
    
    
async def retrieve_value_from_table(configData, tableName, whereColumn, whereValue, column, logger):
    """
    Retrieve a value from a table

    :param configData:
    :param tableName:
    :param whereColumn:
    :param whereValue:
    :param column:
    :param logger:
    :return:
    """

    # Connect to the database
    db = await connect_to_db(configData)
    if db is None:
        exceptionMessage = "Error connecting to the database, please try again later"
        logger.error(exceptionMessage)
        return Exception(exceptionMessage)

    try:
        cursor = db.cursor()
        cursor.execute("SELECT " + column + " FROM " + tableName +
                       " WHERE " + whereColumn + "='" + whereValue + "'")
        value = cursor.fetchone()
        db.close()
        if value is None:
            return None
        return value[0]
    except Exception as e:
        exceptionMessage = "Error retrieving value from database table " + tableName + ": " + str(e)
        logger.error(exceptionMessage)
        db.close()
        return e(exceptionMessage)
