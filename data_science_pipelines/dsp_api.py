import json
import os

from hooks.LanguageHook import LanguageHook
from rule_extractor import RuleExtractor
import db_driver
from graph_extractor import GraphExtractor
from rule_manager import RuleManager
from knowledge_base_manager import KnowledgeBaseManager

class DSP_API():

    def __init__(self):
        self.rule_extractor = RuleExtractor()
        self.graph_extractor = GraphExtractor()
        # self connection to db?
        self.rule_manager = RuleManager()
        self.kb_manager = KnowledgeBaseManager()

        pass

    def init_db(self):
        # adapt so that we pass connection?
        db_driver.reset_db()
        pass

    def create_pipeline(self, code, language, hook:LanguageHook=None, write_to_file=True, output_path="outputs/ds_pipeline.json"):
        graph = self.graph_extractor.extract_pipeline(code, language, hook)
        if write_to_file:
            out_file = open(output_path, "w")
            json.dump(graph, out_file, indent=4)
            out_file.close()
        else:
            return graph

    def extract_rule(self, g1, g2, rule_type):
        pattern, result = self.rule_extractor.extract_rule(g1, g2, rule_type)
        return pattern, result #viz

    def confirm_rule(self, pattern, result, rule_name, rule_description, language, rule_type="syntactic", priority=50):
        rule = self.rule_extractor.adapt_rule(pattern, result, rule_name, rule_description, language, rule_type="syntactic", priority=50)
        return rule

    # how to return the manager correctly so that it is not created every time?
    def list_rules(self, language):
        rule_list = self.rule_manager.list_all_rules(language)
        return rule_list

    def visualize_rule(self, rule_name):
        self.rule_manager.visualize_rule(rule_name)
        pass

    def delete_rule(self, rule_name):
        self.rule_manager.delete_rule_by_name(rule_name)
        pass

    def add_rule(self, rule_dict):
        self.rule_manager.add_rule_to_db(rule_dict)
        pass

    def add_module(self, name, version, date, language):
        self.kb_manager.add_module_to_kb(name, version, date, language)
        pass

    def add_function(self, module_name, function_title, description="", link="", language="", data_science_task="", args=""):
        self.kb_manager.add_function_to_kb(module_name, function_title, description="", link="", language="", data_science_task="", args="")
        pass

    def add_ds_task(self, module_name, function_name, language, ds_task):
        self.kb_manager.add_ds_task_to_kb(module_name, function_name, language, ds_task)
        pass
