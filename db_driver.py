import sqlite3
import csv
from models.Function import Function

connection = sqlite3.connect("knowledge_base.db")
cursor = connection.cursor()


def init_db():
    cursor.execute("drop table functions")
    cursor.execute("drop table arguments")
    cursor.execute("CREATE TABLE functions(module_name, id, title, description, link, PRIMARY KEY (module_name, id))")
    cursor.execute(
        "CREATE TABLE arguments(module_name, title, argument_name, argument_type, argument_position, default_value)")
    return


# todo adapt to ini any
def init_pandas():
    with open("knowledge_base/pandas_kb.csv", newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        header = next(csvreader)
        for row in csvreader:
            # add function values
            function = Function.parse_from_list(row)
            cursor.execute("INSERT INTO functions VALUES(?, ?, ?, ?, ?)",
                           ['pandas', function.index, function.name, function.description, function.link])
            if function.args is not None:
                for arg in function.args:
                    cursor.execute("INSERT INTO arguments VALUES(?, ?, ?, ?, ?, ?)",
                                   ['pandas', function.name, arg.name, arg.type, arg.position, arg.default_value])
    connection.commit()
    return

def test():
    result = Function.parse_from_db(connection, cursor, "pandas", "pandas.HDFStore.append")
    print(result)
    return

#init_db()
#init_pandas()
test()
connection.close()
