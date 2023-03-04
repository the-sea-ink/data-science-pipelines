import json
import unittest
import test_scripts
from hooks.PythonHook import PythonHook
from dsp_api import DSP_API
import utils


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here


def test_extract_rule(api):
    f1 = open('g1.json')
    g1 = json.load(f1)
    f2 = open("g2.json")
    g2 = json.load(f2)
    G1 = utils.json_to_nxgraph(g1)
    G2 = utils.json_to_nxgraph(g2)

    pattern, result = api.extract_rule(G1, G2, "semantic")
    print(pattern)
    print(result)
    pass


def test_graph_extractor(api):
    code = test_scripts.Python.code_0
    language = 'python'
    hook = PythonHook
    write_to_file = True
    output_path = "outputs/ds_pipeline.json"
    api.create_pipeline(code, language, hook, write_to_file, output_path)


if __name__ == '__main__':
    api = DSP_API()
    #test_graph_extractor(api)
    test_extract_rule(api)

