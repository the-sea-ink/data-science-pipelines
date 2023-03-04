import os
import sqlite3

from networkx.algorithms.isomorphism import GraphMatcher
from regraph import NXGraph, Rule
import time
import utils
from hooks.LanguageHook import LanguageHook
from rule_extractor import RuleExtractor
from utils import print_graph, read_rule_from_string, convert_graph_to_json_new_frontend, nxgraph_to_json
from models.Function import Function
from rule_manager import get_rules_from_db

STR_NODE_ID = "node_id"
STR_ATTR_NAME = "attr_name"
STR_ATTR_VALUE = "attr_value"


class TransformationPipeline:

    def __init__(self, language):
        self.connection = sqlite3.connect("../knowledge_base.db")
        self.cursor = self.connection.cursor()
        self.language = language

    def knowledge_base_lookup(self, G: NXGraph, module_node_attr="module",
                              full_function_call_attr="full_function_name"):
        # search for nodes with "full_function_name" attribute
        for node, attrs in G.nodes(True):
            if full_function_call_attr in attrs.keys() and module_node_attr in attrs.keys():
                title_to_lookup = next(iter(attrs[full_function_call_attr]))
                module_to_lookup = next(iter(attrs[module_node_attr]))
                function = Function.get_function_by_name_module_language(self.cursor, module_to_lookup,
                                                                         title_to_lookup, self.language)
                if function is not None:
                    enriched_node_attrs = attrs.copy()
                    enriched_node_attrs["description"] = function.description
                    enriched_node_attrs["link"] = function.link
                    enriched_node_attrs["data_science_task"] = function.ds_task
                    enriched_node_attrs["arguments"] = list(function.args)
                    G.update_node_attrs(node, enriched_node_attrs)
        return G


def flip_tree(G: NXGraph):
    """
    Turns the initial tree upside down, allows for better rules definition
    and application.

    :param G: an NXGraph object
    """
    root_node = utils.get_root_node_id(G)
    flip_node(G, root_node)


def flip_node(G: NXGraph, node_to_flip, id_to_ignore=-1):
    if not G.successors(node_to_flip):
        return
    children = list()
    for child in G.successors(node_to_flip):
        children.append(child)
    while children:
        child = children.pop(0)
        if child == id_to_ignore:
            continue
        G.add_edge(child, node_to_flip)
        G.remove_edge(node_to_flip, child)
        flip_node(G, child, node_to_flip)


def add_labels(G: NXGraph):
    """
    Adds labels that will be displayed in the front-end.

    :param G: an NXGraph object
    """
    nodes = G.nodes()
    for node_id in nodes:
        node = G.get_node(node_id)
        node_text = node["text"]
        G.add_node_attrs(node_id, {"label": node_text})


def process_wildcard_attributes(rule: NXGraph, G: NXGraph, rule_string):
    pattern = rule.lhs
    wildcards = {}

    for node, attrs in pattern.nodes(True):
        for attribute in attrs:
            for elem in attrs[attribute]:
                if "%unknown_value" in elem:
                    # create a list of wildcard node occurrences
                    if elem not in wildcards.keys():
                        wildcards[elem] = []
                    wildcards[elem].append((node, attribute))

    generalized_pattern = pattern.copy(pattern)
    if len(wildcards) == 0:
        return [rule]
    for wildcard, wildcard_occurrances in wildcards.items():
        for occurance in wildcard_occurrances:
            generalized_pattern.remove_node_attrs(occurance[0],
                                                  {occurance[1]: wildcard})
    instances = find_matching_optimised(G, generalized_pattern)

    wildcard_answers = []

    for generalized_instance in instances:
        wildcard_matches = {}
        for wildcard, wildcard_occurrances in wildcards.items():
            node_id_with_wildcard = wildcard_occurrances[0][0]
            attribute_name_with_wildcard = wildcard_occurrances[0][1]
            mached_node_id = generalized_instance[node_id_with_wildcard]
            wildcard_value = G.get_node_attrs(mached_node_id)[attribute_name_with_wildcard]
            wildcard_value = next(iter(wildcard_value))
            wildcard_matches[wildcard] = wildcard_value
        correct = True
        for wildcard, wildcard_occurrances in wildcards.items():
            if not correct:
                break
            for occurance in wildcard_occurrances:
                node_id_with_wildcard = occurance[0]
                attribute_name_with_wildcard = occurance[1]
                mached_node_id = generalized_instance[node_id_with_wildcard]
                node_attrs = G.get_node_attrs(mached_node_id)
                expected_value = node_attrs[attribute_name_with_wildcard]
                if next(iter(expected_value)) != wildcard_matches[wildcard]:
                    correct = False
                    break
        if not correct:
            continue

        duplicate = False
        for rule_answer in wildcard_answers:
            shared_wildcard_values = {k: rule_answer[k] for k in rule_answer if
                                      k in wildcard_matches and rule_answer[k] == wildcard_matches[k]}
            if len(shared_wildcard_values) == len(rule_answer):
                duplicate = True
                break
        if not duplicate:
            wildcard_answers.append(wildcard_matches)
    rules = []
    for answer in wildcard_answers:
        new_rule_string = str(rule_string)
        for wildcard, wildcard_value in answer.items():
            if type(wildcard_value) is str:
                wildcard_value = wildcard_value.replace("'", "\\\'")
            new_rule_string = new_rule_string.replace(wildcard, wildcard_value)
        json_rule = read_rule_from_string(new_rule_string)
        rules.append(Rule.from_json(json_rule))
    return rules


def node_comparator(graph_node_attrs, pattern_node_attrs):
    if len(pattern_node_attrs) == 0:
        return True
    for (key, value) in pattern_node_attrs.items():
        if (key, value) not in graph_node_attrs.items():
            return False
    return True


def find_matching_optimised(G, pattern):
    # utils.print_graph(G)
    instances = []
    gm = GraphMatcher(utils.nxraph_to_digraph(G), utils.nxraph_to_digraph(pattern),
                      node_comparator)
    s = list(gm.subgraph_isomorphisms_iter())
    optimited_instances = list()
    for elem in s:
        optimited_instances.append({v: k for k, v in elem.items()})
    return optimited_instances


def find_connected_graph(G, pattern):
    instances = []
    # get subgraphs for faster instance finding
    subgraphs = utils.get_ascendant_subgraphs_by_pattern(G, pattern)
    for subgraph in subgraphs:
        instances.extend(G.find_matching(pattern, subgraph))
    return instances


def apply_rule(G, rule_string: str):
    """
    Applies given rule on a graph.

    :param G: an NXGraph object
    :param rule_string: rule instance
    """

    json_rule = read_rule_from_string(rule_string)

    rule = Rule.from_json(json_rule)

    rules = process_wildcard_attributes(rule, G, rule_string)
    # check for wild card in pattern nodes

    for rule in rules:
        pattern = rule.lhs
        instances = find_matching_optimised(G, pattern)

        if instances:
            # print(instances)

            for instance in instances:
                G.rewrite(rule, instance)
    return G


def test_func(G):
        # search for all calls or attributes
        for node, attrs in G.nodes(True):
            if (next(iter(attrs["type"])) == "call" or next(
                    iter(attrs["type"])) == "attribute") and "full_function_name" not in attrs.keys():
                new_node_attrs = attrs.copy()
                new_node_attrs["full_function_name"] = attrs["text"]
                new_node_attrs["module"] = "built-in"
                G.update_node_attrs(node, new_node_attrs)
        return G

def transform_graph(G: NXGraph, language, language_specific_hook:LanguageHook):
    """
    Applies rules from the rule base and further transformations to the given graph.

    :param G: an NXGraph object
    :return: graph in a json format
    """
    pipeline = TransformationPipeline(language)
    #hook = language_specific_hook()
    start_iner = time.time()

    # connect to db
    db_path = os.path.join(os.path.dirname(__file__), "../knowledge_base.db")
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # initial graph transformation
    flip_tree(G)
    utils.print_graph(G)

    hook = language_specific_hook
    #hook.pre_hooks(G)


    end_iner = time.time()
    print(f'pre transformations done in {end_iner - start_iner}')
    start_outer = time.time()

    # apply rules from rule base one by one
    rules = get_rules_from_db(cursor)
    for counter, rule in enumerate(rules, 1):
        start_iner = time.time()
        json_rule = read_rule_from_string(rule[0])
        print(f'Applying rule #{counter}')
        # utils.draw_rule()
        # print(rule)
        # utils.draw_rule(counter)
        G = apply_rule(G, rule[0])
        print_graph(G)
        # print_graph(G)
        end_iner = time.time()
        #if end_iner - start_iner > 3:
            #utils.draw_rule(counter)
        # print(f'line {counter} done in {end_iner - start_iner}')
    end_outer = time.time()
    # print(f'apply rule  done in {end_outer - start_outer}')
    start_iner = time.time()

    #test_func(G)

    #hook.post_hooks(G)
    pipeline.knowledge_base_lookup(G)

    end_iner = time.time()
    print(f'post transformations done in {end_iner - start_iner}')
    print_graph(G)
    #draw_graph(G)
    graph_dict = nxgraph_to_json(G)
    print(graph_dict)

    pseudo_graph = utils.json_to_nxgraph(graph_dict)
    print_graph(pseudo_graph)

    connection.close()
    return graph_dict


if __name__ == "__main__":
    utils.draw_rule(15, RuleExtractor())
    pass
