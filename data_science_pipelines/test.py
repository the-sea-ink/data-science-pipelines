import json
import unittest
import test_scripts
from evaluation.stat_collector import StatCollector
from hooks.PythonHook import PythonHook
from dsp_api import DSP_API
import utils
from evaluation.scripts import scripts


class MyTestCase(unittest.TestCase):

    def test_something(self):
        self.assertEqual(True, False)  # add assertion here


def test_graph_extractor(api):
    code = test_scripts.Python.code_0
    language = 'python'
    hook = PythonHook()
    write_to_file = True
    output_path = "evaluation/outputs/ds_pipeline.json"
    api.create_pipeline(code, language, hook, write_to_file, output_path)


def test_extract_rule(api):
    f1 = open('evaluation/g1.json')
    g1 = json.load(f1)
    f2 = open("evaluation/g2.json")
    g2 = json.load(f2)
    G1 = utils.json_to_nxgraph(g1)
    G2 = utils.json_to_nxgraph(g2)

    pattern, result = api.extract_rule(G1, G2, "semantic")
    print(pattern)
    print(result)
    return pattern, result


def test_confirm_rule(api, pattern, result):
    rule = api.confirm_rule(pattern, result, "testname", "testdescr", "python", "semantic", 50)
    print(rule)


def test_list_rules(api):
    print(api.list_rules("python"))
    pass


def test_delete_rule(api):
    print(api.delete_rule("testname"))
    pass


def test_add_rule(api):
    f = open("knowledge_base/rules/rule_creation.json", "r")
    rule_dict = json.loads(f.read())
    api.add_rule(rule_dict)
    pass


def test_add_module(api):
    print(api.add_module("test_module", "1.2.3", "2023-12-15", "python"))
    pass


def test_add_function(api):
    print(api.add_function("test_module", "test_func", description="1234", link="345", language="python",
                           data_science_task="fewrg", args="e=1"))


def test_add_ds_task(api):
    print(api.add_ds_task("test_module", "test_func", "python", "test_task"))


def evaluate_script_collection(api):

    code = test_scripts.Python.code_0
    language = 'python'
    hook = PythonHook()
    write_to_file = False
    #print(len(scripts))
    #api.create_pipeline(scripts["sklearn12"]["script"], language, hook, write_to_file)
    stat = StatCollector.getStatCollector()
    stat.collecting_data = True
    counter = 0
    for scr in scripts:
        print(scr)
        if not scr == 'kaggle10':
            continue
        stat.new_script()
        stat.append_script_data({'script name': scr})
        api.create_pipeline(scripts[scr]["script"], language, hook, write_to_file)
        stat.store_script_and_rule_dataframe()
        stat.export_data()
    stat.print()


if __name__ == '__main__':
    api = DSP_API()
    # test_graph_extractor(api)
    # pattern, result = test_extract_rule(api)
    # test_confirm_rule(api, pattern, result)
    # test_list_rules(api)
    # test_delete_rule(api)
    # test_add_rule(api)
    # test_add_module(api)
    # test_add_function(api)
    # test_add_ds_task(api)
    evaluate_script_collection(api)
