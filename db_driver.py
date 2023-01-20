import datetime
import sqlite3
import csv
from models.Function import Function


def init_db(cursor):
    """
    Initializes database.

    Creates empty tables "modules", "function", "arguments".
    :param cursor: connection cursor
    """
    cursor.execute("DROP TABLE functions")
    cursor.execute("DROP TABLE arguments")
    cursor.execute("DROP TABLE modules")
    cursor.execute("CREATE TABLE modules(module_id INTEGER NOT NULL, module_name PRIMARY KEY, version, date)")
    cursor.execute(
        "CREATE TABLE functions(function_id INTEGER PRIMARY KEY, module_name, function_title type UNIQUE, description, link, FOREIGN KEY(module_name) REFERENCES modules(module_name))")
    cursor.execute(
        "CREATE TABLE arguments(function_id, argument_name, argument_type, argument_position, default_value, FOREIGN KEY(function_id) REFERENCES functions(function_id))")


def init_module(filename, module_name, version, date, cursor):
    with open(filename, newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        header = next(csvreader)
        cursor.execute("SELECT COUNT(*) FROM modules")
        module_id = cursor.fetchall()[0][0] + 1
        # add module info
        cursor.execute("INSERT INTO modules(module_id, module_name, version, date) VALUES(?, ?, ?, ?)",
                       [module_id, module_name, version, date])
        for (index, row) in enumerate(csvreader):
            function = Function.parse_from_list(row)
            # add function values
            cursor.execute("INSERT INTO functions(module_name, function_title, description, link) VALUES(?, ?, ?, ?)",
                           [module_name, function.name, function.description, function.link])
            added_function_id = cursor.lastrowid
            if function.args is not None:
                for arg in function.args:
                    cursor.execute("INSERT INTO arguments VALUES(?, ?, ?, ?, ?)",
                                   [added_function_id, arg.name, arg.type, arg.position, arg.default_value])
    connection.commit()


if __name__ == "__main__":
    connection = sqlite3.connect("knowledge_base.db")
    cursor = connection.cursor()
    init_db(cursor)
    date = datetime.date(2023, 1, 17)
    init_module("knowledge_base/pandas 2023-1-17 1.5.2.csv", "pandas", "1.5.2", date, cursor)
    init_module("knowledge_base/sklearn 2023-1-17 1.2.0.csv", "sklearn", "1.2.0", date, cursor)
    connection.close()

