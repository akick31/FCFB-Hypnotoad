import logging

from fcfb.database.connection import connect_to_db


async def add_row_to_table(configData, schema, tableName, columnNames, values, logger):
    """
    Add a row to a table

    :param configData:
    :param schema:
    :param tableName:
    :param columnNames:
    :param values:
    :param logger:
    :return:
    """

    try:
        # Connect to the database
        db = await connect_to_db(configData, schema, logger)

        cursor = db.cursor()
        command = "INSERT INTO " + tableName + " (" + columnNames + ") VALUES (" + values + ")"
        cursor.execute(command)
        db.commit()
        db.close()
        return
    except Exception as e:
        exceptionMessage = "Error adding row to database table " + tableName + ": " + str(e)
        logger.error(exceptionMessage)
        db.close()
        return e(exceptionMessage)


async def retrieve_row_from_table(configData, schema, tableName, whereColumn, whereValue, logger):
    """
    Retrieve a row in a table

    :param configData:
    :param schema:
    :param tableName:
    :param whereColumn:
    :param whereValue:
    :param logger:
    :return:
    """

    try:
        # Connect to the database
        db = await connect_to_db(configData, schema, logger)

        cursor = db.cursor()
        cursor.execute("SELECT * FROM " + tableName +
                       " WHERE UPPER(" + whereColumn + ") LIKE UPPER('" + whereValue + "')")
        row = cursor.fetchall()
        db.close()
        if row is None:
            raise Exception("Row not in database")
        return row
    except Exception as e:
        exceptionMessage = "Error retrieving row from database table " + tableName + ": " + str(e)
        logger.error(exceptionMessage)
        db.close()
        raise e(exceptionMessage)
    
    
async def retrieve_value_from_table(configData, schema, tableName, whereColumn, whereValue, column, logger):
    """
    Retrieve a value from a table

    :param configData:
    :param schema:
    :param tableName:
    :param whereColumn:
    :param whereValue:
    :param column:
    :param logger:
    :return:
    """

    try:
        # Connect to the database
        db = await connect_to_db(configData, schema, logger)

        cursor = db.cursor()
        cursor.execute("SELECT " + column + " FROM " + tableName +
                       " WHERE " + whereColumn + "='" + whereValue + "'")
        value = cursor.fetchone()
        db.close()
        if value is None:
            raise Exception("Value not in database")
        return value[0]
    except Exception as e:
        exceptionMessage = "Error retrieving value from database table " + tableName + ": " + str(e)
        logger.error(exceptionMessage)
        db.close()
        raise e(exceptionMessage)
