import argparse
import os
import sys

import test_scripts
from rule_manager import RuleManager
from graph_extractor import GraphExtractor


def print_info():
    print("type help to see help")


def get_hook(path):
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location("language_hook", path)
    hook_module = importlib.util.module_from_spec(spec)
    sys.modules["language_hook"] = hook_module
    spec.loader.exec_module(hook_module)
    return hook_module.LanguageHook()


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return open(arg, 'r')  # return an open file handle


def is_valid_rule_type(parser, arg):
    if arg not in [RuleManager.RULE_TYPE_SYNTACT, RuleManager.RULE_TYPE_SEMANT]:
        parser.error(f'{arg} is not a valid rule type!'
                     f' Use {RuleManager.RULE_TYPE_SYNTACT} or {RuleManager.RULE_TYPE_SEMANT} instead.')
    else:
        return arg


def process_init_db(args):
    pass


def process_create_pipeline(args):
    pass


def process_extract_rule(args):
    print(args.g1)
    print(args.g2)
    print(args.type)


def process_confirm_rule(args):
    pass


def process_list_rules(args):
    pass


def process_visualize_rule(args):
    pass


def process_delete_rule(args):
    pass


def process_add_rule(args):
    pass


def process_add_module(args):
    pass


def process_add_function(args):
    pass


def process_add_ds_task(args):
    pass


def process_cli(argv):
    parser = argparse.ArgumentParser()
    cmd_parser = parser.add_subparsers(dest='command')

    # creating command parsers
    cmd_init_db = cmd_parser.add_parser("init_db")
    cmd_create_pipeline = cmd_parser.add_parser("create_pipeline")
    cmd_extract_rule = cmd_parser.add_parser("extract_rule")
    cmd_confirm_rule = cmd_parser.add_parser("confirm_rule")
    cmd_list_rules = cmd_parser.add_parser("list_rules")
    cmd_visualize_rule = cmd_parser.add_parser("visualize_rule")
    cmd_delete_rule = cmd_parser.add_parser("delete_rule")
    cmd_add_rule = cmd_parser.add_parser("add_rule")
    cmd_add_module = cmd_parser.add_parser("add_module")
    cmd_add_function = cmd_parser.add_parser("add_function")
    cmd_add_ds_task = cmd_parser.add_parser("add_ds_task")

    # configuring command parsers
    cmd_extract_rule.add_argument("g1",
                                  help="path to first graph", metavar="graph_1",
                                  type=lambda x: is_valid_file(parser, x))
    cmd_extract_rule.add_argument("g2",
                                  help="path to second graph", metavar="graph_2",
                                  type=lambda x: is_valid_file(parser, x))
    cmd_extract_rule.add_argument("type",
                                  help="rule type to be created", metavar="rule type",
                                  type=lambda x: is_valid_rule_type(parser, x))
    args = parser.parse_args()
    if args.command == 'init_db':
        process_init_db(args)
    elif args.command == 'extract_rule':
        process_extract_rule(args)
    return


def extract_graph(external_language_extension=None):
    language = 'python'
    code = test_scripts.Python.code_0
    extractor = GraphExtractor()
    language_hook = None
    if external_language_extension is not None:
        language_hook = external_language_extension
    extractor.extract_pipeline(code, language, language_hook)


if __name__ == "__main__":
    process_cli(sys.argv)
