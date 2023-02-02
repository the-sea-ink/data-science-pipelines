import datetime
import sqlite3
import csv
import os
from models.Function import Function
import utils
import json
import yaml
import io
from utils import read_rule_from_string
import pprint


def init_db(cursor):
    """
    Initializes database.

    Creates empty tables "modules", "function", "arguments", "rules".
    :param cursor: connection cursor
    """
    cursor.execute("DROP TABLE IF EXISTS functions")
    cursor.execute("DROP TABLE IF EXISTS arguments")
    cursor.execute("DROP TABLE IF EXISTS modules")
    cursor.execute("DROP TABLE IF EXISTS rules")
    cursor.execute(
        "CREATE TABLE modules(module_id INTEGER NOT NULL, module_name PRIMARY KEY, version, date)")
    cursor.execute(
        "CREATE TABLE functions(function_id INTEGER PRIMARY KEY, module_name, function_title type UNIQUE, "
        "description, link, FOREIGN KEY(module_name) REFERENCES modules(module_name))")
    cursor.execute(
        "CREATE TABLE arguments(function_id, argument_name, argument_type, argument_position, default_value, "
        "FOREIGN KEY(function_id) REFERENCES functions(function_id))")
    cursor.execute(
        "CREATE TABLE rules(rule_id, rule_name PRIMARY KEY, rule_description, rule, rule_type, added_by_user)")
    connection.commit()


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


def init_ds_tasks():
    """
    Parses data science ontology library into a dictionary and
    dumps it into a json file.
    """
    ds_tasks = {}

    # find all yaml files
    yaml_files = []

    for path, subdirs, files in os.walk("knowledge_base/annotation"):
        for name in files:
            file_path = os.path.join(path, name)
            yaml_files.append(file_path)

    for file in yaml_files:
        with open(file) as stream:
            data_loaded = yaml.safe_load(stream)
            if type(data_loaded["definition"]) is list:
                continue
            if "class" in data_loaded.keys():
                if type(data_loaded["class"]) is list:
                    for class_name in data_loaded["class"]:
                        ds_tasks[class_name] = data_loaded["definition"]
                else:
                    ds_tasks[data_loaded["class"]] = data_loaded["definition"]
            elif "function" in data_loaded.keys():
                ds_tasks[data_loaded["function"]] = data_loaded["definition"]

    # save result into json
    json_object = json.dumps(ds_tasks, indent=2)
    with open("knowledge_base/ds_tasks.json", "w") as outfile:
        outfile.write(json_object)


def init_rules_from_file():
    cursor.execute("SELECT COUNT(*) FROM rules")
    added_rule_id = cursor.fetchall()[0][0] + 1
    with open("knowledge_base/rule_base.txt") as file:
        for counter, line in enumerate(file, 1):
            json_rule = read_rule_from_string(line)
            if "name" in json_rule:
                rule_name = json_rule.pop("name")
            if "description" in json_rule:
                rule_desc = json_rule.pop("description")
            if "type" in json_rule:
                rule_type = json_rule.pop("rule_type")
            else:
                rule_type = "syntactic"
            added_by_user = False
            cursor.execute(
                "INSERT INTO rules(rule_id, rule_name, rule_description, rule, rule_type, added_by_user) VALUES(?, ?, ?, ?, ?, ?)",
                [added_rule_id, rule_name, rule_desc, str(json_rule), rule_type, added_by_user])
            added_rule_id = cursor.lastrowid
    connection.commit()
    pass


if __name__ == "__main__":
    connection = sqlite3.connect("knowledge_base.db")
    cursor = connection.cursor()
    init_db(cursor)
    init_ds_tasks()
    files = os.listdir("knowledge_base/modules/")
    for file in files:
        module_name, date, version = file.replace(".csv", "").split(" ")
        date_format = "%Y-%m-%d"
        date = datetime.datetime.strptime(date, date_format).date()
        module_path = "knowledge_base/modules/" + file
        init_module(module_path, module_name, version, date, cursor)
    init_rules_from_file()
    connection.close()
