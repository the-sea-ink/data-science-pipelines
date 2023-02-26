import argparse
import os
import sys
import datetime
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


def is_date_valid(parser, arg):
    try:
        datetime.date.fromisoformat(arg)
    except ValueError:
        parser.error(f'{arg} is not a valid data format! Date should be in a format YYYY-MM-DD')
    return arg


def is_valid_date_type(parser, arg):
    pass


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

    # configuring create pipeline
    cmd_create_pipeline.add_argument("script_path",
                                  help="path to a script to be transformed into a pipeline", metavar="path to script file",
                                  type=lambda x: is_valid_file(parser, x))
    cmd_create_pipeline.add_argument("script_language",
                                     help="script language", metavar="script language",
                                     type=str)
    cmd_create_pipeline.add_argument("hook", dest="hook_path", required=False,
                                    help="path to an external hook for pre and post transformations of the pipeline", metavar="hook",
                                    type=lambda x: is_valid_file(parser, x))

    cmd_create_pipeline.add_argument("-o", dest="output_path", required=False,
                                     help="path to the file with the output graph",
                                     metavar="out_path",
                                     type=lambda x: is_valid_file(parser, x))

    # configuring extract rule
    cmd_extract_rule.add_argument("g1",
                                  help="path to first graph", metavar="graph_1",
                                  type=lambda x: is_valid_file(parser, x))
    cmd_extract_rule.add_argument("g2",
                                  help="path to second graph", metavar="graph_2",
                                  type=lambda x: is_valid_file(parser, x))
    cmd_extract_rule.add_argument("type",
                                  help="rule type to be created", metavar="rule type",
                                  type=lambda x: is_valid_rule_type(parser, x))

    # configuring confirm rule
    cmd_confirm_rule.add_argument("PaT",
                                  help="path to PaT rule", metavar="PaT",
                                  type=lambda x: is_valid_file(parser, x))

    cmd_confirm_rule.add_argument("rule_name",
                                  help="rule name", metavar="rule_name",
                                  type=str)

    cmd_confirm_rule.add_argument("rule_description",
                                  help="rule description", metavar="rule_description",
                                  type=str)

    cmd_confirm_rule.add_argument("rule_language",
                                  help="rule language", metavar="rule_language",
                                  type=str)

    # configuring list rules
    cmd_list_rules.add_argument("language",
                                  help="list rules by language", metavar="language",
                                  type=str)

    # configuring visualize rule
    cmd_visualize_rule.add_argument("rule_name",
                                  help="creates a visualisation of a rule by rule name", metavar="rule_name",
                                  type=str)

    # configuring delete rule
    cmd_delete_rule.add_argument("rule_name",
                                  help="removes a rule by rule name", metavar="rule_name",
                                  type=str)

    # configuring add rule
    cmd_add_rule.add_argument("path to PaT rule",
                                  help="path to PaT rule", metavar="PaT",
                                  type=lambda x: is_valid_file(parser, x))

    # configuring add module
    cmd_add_module.add_argument("module_name",
                                  help="module name", metavar="module_name",
                                  type=str)

    cmd_add_module.add_argument("module_version",
                                help="module version", metavar="module_version",
                                type=str)

    cmd_add_module.add_argument("module_date",
                                help="date when module was scraped in a format yyyy-mm-dd", metavar="date",
                                type=str)

    cmd_add_module.add_argument("module_language",
                                help="module language", metavar="module_language",
                                type=str)

    # configuring add function
    cmd_add_function.add_argument("module_name", type=str)
    cmd_add_function.add_argument("function_title", type=str)
    cmd_add_function.add_argument("function_description", type=str)
    cmd_add_function.add_argument("function_language", type=str)
    cmd_add_function.add_argument("ds_task", type=str)
    cmd_add_function.add_argument("link", dest="doc_link", required=False,
                                    help="link to documentation", metavar="link",
                                    type=str)
    cmd_add_function.add_argument("args", dest="func_args", required=False,
                                  help="function arguments in a string format, comma separated", metavar="args",
                                  type=str)

    # configuring add ds task
    cmd_add_ds_task.add_argument("module_name", type=str)
    cmd_add_ds_task.add_argument("function_title", type=str)
    cmd_add_ds_task.add_argument("language", type=str)
    cmd_add_ds_task.add_argument("ds_task", type=str)











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
