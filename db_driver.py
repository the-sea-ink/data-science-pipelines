import sqlite3
import csv
from models.Function import Function

connection = sqlite3.connect("knowledge_base.db")
cursor = connection.cursor()


def init_db():
    cursor.execute("drop table functions")
    cursor.execute("drop table arguments")
    cursor.execute("CREATE TABLE functions(function_id INTEGER PRIMARY KEY, module_name, function_title type UNIQUE, description, link)")
    cursor.execute(
        "CREATE TABLE arguments(function_id, argument_name, argument_type, argument_position, default_value, FOREIGN KEY(function_id) REFERENCES functions(function_id))")
    return


# todo adapt to ini any
def init_module(filename, module_name):
    with open(filename, newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        header = next(csvreader)
        for row in csvreader:
            # add function values
            function = Function.parse_from_list(row)
            cursor.execute("INSERT INTO functions(module_name, function_title, description, link) VALUES(?, ?, ?, ?)",
                           [module_name, function.name, function.description, function.link])
            added_function_id = cursor.lastrowid
            if function.args is not None:
                for arg in function.args:
                    cursor.execute("INSERT INTO arguments VALUES(?, ?, ?, ?, ?)",
                                   [added_function_id, arg.name, arg.type, arg.position, arg.default_value])
    connection.commit()
    return

def test():
    #init_db()
    #init_module("knowledge_base/pandas.csv", "pandas")
    #init_module("knowledge_base/sklearn.csv", "sklearn")
    result = Function.parse_from_db(cursor, "sklearn", "sklearn.utils.validation.has_fit_parameter")
    print(result)
    return

test()
connection.close()
