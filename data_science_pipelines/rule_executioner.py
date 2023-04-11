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
                              full_function_call_attr="full_function_call"):
        # search for nodes with "full_function_call" attribute
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

    # 1
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

    # 2
    for wildcard, wildcard_occurrances in wildcards.items():
        for occurance in wildcard_occurrances:
            generalized_pattern.remove_node_attrs(occurance[0],
                                                  {occurance[1]: wildcard})

    # 3
    instances = find_matching_optimised(G, generalized_pattern)
    wildcard_answers = []

    for generalized_instance in instances:
        wildcard_matches = {}
        # 4
        for wildcard, wildcard_occurrances in wildcards.items():
            pattern_node_id_with_wildcard = wildcard_occurrances[0][0]
            attribute_name_with_wildcard = wildcard_occurrances[0][1]
            mached_node_id = generalized_instance[pattern_node_id_with_wildcard]
            wildcard_value = G.get_node_attrs(mached_node_id)[attribute_name_with_wildcard]
            wildcard_value = next(iter(wildcard_value))
            wildcard_matches[wildcard] = wildcard_value
        # 5.1
        if len(wildcard_matches) != len(set(wildcard_matches.values())):
            continue
        # 5.2
        correct = True
        for wildcard, wildcard_occurrances in wildcards.items():
            if not correct:
                break
            for occurance in wildcard_occurrances:
                pattern_node_id_with_wildcard = occurance[0]
                attribute_name_with_wildcard = occurance[1]
                mached_node_id = generalized_instance[pattern_node_id_with_wildcard]
                node_attrs = G.get_node_attrs(mached_node_id)
                expected_value = node_attrs[attribute_name_with_wildcard]
                if next(iter(expected_value)) != wildcard_matches[wildcard]:
                    correct = False
                    break
        if not correct:
            continue
        # 6
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
        #instances = G.find_matching(pattern)
        if instances:
            # print(instances)

            for instance in instances:
                G.rewrite(rule, instance)
    return G


def test_func(G):
        # search for all calls or attributes
        for node, attrs in G.nodes(True):
            if (next(iter(attrs["type"])) == "call" or next(
                    iter(attrs["type"])) == "attribute") and "full_function_call" not in attrs.keys():
                new_node_attrs = attrs.copy()
                new_node_attrs["full_function_call"] = attrs["text"]
                new_node_attrs["module"] = "built-in"
                G.update_node_attrs(node, new_node_attrs)
        return G

def propagate(G:NXGraph, node_id):
    visited = set()
    to_visit = set()
    to_visit.add(node_id)
    while len(to_visit) > 0:
        visiting = to_visit.pop()
        visited.add(visiting)
        for neighbour in G.ancestors(node_id).union(G.descendants(node_id)):
            if neighbour not in visited and neighbour not in to_visit:
                to_visit.add(neighbour)
    return list(visited)




def establish_connections(G):
    # find pairs of variables
    instances = list()

    pattern = NXGraph()
    pattern.add_node(1, {'type': 'output_variable', 'text': '%unknown_value1'})
    pattern.add_node(2, {'type': 'identifier', 'text': '%unknown_value1'})
    pattern.add_node(3)
    pattern.add_edge(2, 3)

    rule = Rule.from_transform(pattern)
    rules = process_wildcard_attributes(rule, G, str(rule.to_json()))

    for rule in rules:
        instances.extend(find_matching_optimised(G, rule.lhs))

    #print(instances)
    output_variables = list(set([instance[1] for instance in instances]))
    identifiers = list(set([instance[2] for instance in instances]))
    priorities = {}
    for node in output_variables + identifiers:
        cloud_ids = propagate(G, node)
        priorities[node] = min(cloud_ids)
    #print(priorities)
    new_instances = list()
    for identifier in identifiers:
        new_instance = {}
        #find all output variables that have lower priority than current identifier
        # AND represent the same variable
        lover_ovs = [ov for ov in output_variables if priorities[ov] < priorities[identifier] and G.get_node_attrs(ov)['text']==G.get_node_attrs(identifier)['text']]
        ov_with_highest_prio = lover_ovs[0]
        for ov in lover_ovs:
            if priorities[ov] > priorities[ov_with_highest_prio]:
                ov_with_highest_prio = ov
        #OV with the highest priority is our OV
        old_instance_identifier_output = [instance for instance in instances if instance[2] == identifier][0][3]
        new_instance[1] = ov_with_highest_prio
        new_instance[2] = identifier
        new_instance[3] = old_instance_identifier_output
        new_instances.append(new_instance)
    #print(new_instances)

    rule = Rule.from_transform(pattern)
    rule.inject_add_edge(1, 3)
    rule.inject_remove_node(2)

    for instance in new_instances:
        G.rewrite(rule, instance)

    save_idents = "{'priority' :100,'language': 'python', 'lhs': {'edges': [{'from': 1, 'to': 2, 'attrs': {}}], 'nodes': [{'id': 1, 'attrs': {'type': {'type': 'FiniteSet', 'data': ['identifier']}, 'text': {'type': 'FiniteSet', 'data': ['%unknown_value1']}}}, {'id': 2, 'attrs': {}}]}, 'p': {'edges': [], 'nodes': [{'id': 2, 'attrs': {}}]}, 'rhs': {'edges': [], 'nodes': [{'id': 2, 'attrs': {'identifier': {'type': 'FiniteSet', 'data': ['%unknown_value1']}}}]}, 'p_lhs': {2: 2}, 'p_rhs': {2: 2}, 'name': 'save_leftover_idents', 'description': '', 'rule_type': 'syntactic', 'by_user': False}"
    remove_idents = "{'lhs': {'edges': [], 'nodes': [{'id': 1, 'attrs': {'type': {'type': 'FiniteSet', 'data': ['identifier']}}}]}, 'p': {'edges': [], 'nodes': []}, 'rhs': {'edges': [], 'nodes': []}, 'p_lhs': {}, 'p_rhs': {}, 'name': 'rm_leftover_idents', 'description': 'removes leftover identifiers without connections', 'rule_type': 'syntactic', 'by_user': False}"
    apply_rule(G, save_idents)
    apply_rule(G, remove_idents)

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

    #utils.draw_graph(G, "text")

    # initial graph transformation
    flip_tree(G)

    #utils.draw_graph(G, "text")

    #utils.print_graph(G)

    #language_specific_hook
    if language_specific_hook:
        language_specific_hook.pre_hooks(G)


    end_iner = time.time()
    #print(f'pre transformations done in {end_iner - start_iner}')
    start_outer = time.time()

    # apply rules from rule base one by one
    rules = get_rules_from_db(cursor)
    for counter, rule in enumerate(rules, 1):
        start_iner = time.time()
        json_rule = read_rule_from_string(rule[0])
        #print(f'Applying rule #{counter}')
        # utils.draw_rule()
        # print(rule)
        # utils.draw_rule(counter)
        #if counter == 33:
            #print("yo")
        G = apply_rule(G, rule[0])
        #print_graph(G)
        # print_graph(G)
        end_iner = time.time()
        #if end_iner - start_iner > 3:
            #utils.draw_rule(counter)
        # print(f'line {counter} done in {end_iner - start_iner}')
    end_outer = time.time()
    # print(f'apply rule  done in {end_outer - start_outer}')
    start_iner = time.time()

    #utils.draw_graph(G, "text")

    establish_connections(G)
    #test_func(G)

    if language_specific_hook:
        language_specific_hook.post_hooks(G)


    pipeline.knowledge_base_lookup(G)

    end_iner = time.time()
    #print(f'post transformations done in {end_iner - start_iner}')
    #print_graph(G)
    #draw_graph(G)
    graph_dict = nxgraph_to_json(G)
    #print(graph_dict)

    pseudo_graph = utils.json_to_nxgraph(graph_dict)
    #print_graph(pseudo_graph)

    #utils.draw_graph(G, "text")
    connection.close()
    return graph_dict


if __name__ == "__main__":
    for i in [66]:
        utils.draw_rule(i, RuleExtractor())
    pass
