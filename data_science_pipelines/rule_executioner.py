import os
import sqlite3
from functools import partial
from multiprocessing import Pool

import regraph
from networkx.algorithms.isomorphism import GraphMatcher
from regraph import NXGraph, Rule, find_matching
import time
import utils
from evaluation.stat_collector import StatCollector
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
    #StatCollector.getStatCollector().append_rule_data({'wildcard amount': len(wildcards)})
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
    #StatCollector.getStatCollector().append_rule_data({'generalized instances': len(instances)})

    instances_without_needed_attributes = list()
    for instance in instances:
        for node_attr_list in wildcards.values():
            for node_attr in node_attr_list:
                pattern_node_id = node_attr[0]
                graph_node_id = instance[pattern_node_id]
                needed_attr = node_attr[1]
                if needed_attr not in G.get_node_attrs(graph_node_id):
                    instances_without_needed_attributes.append(instance)
    for instance_to_delete in instances_without_needed_attributes:
        instances.remove(instance_to_delete)

    for generalized_instance in instances:
        wildcard_matches = {}
        # 4
        for wildcard, wildcard_occurrances in wildcards.items():
            pattern_node_id_with_wildcard = wildcard_occurrances[0][0]
            attribute_name_with_wildcard = wildcard_occurrances[0][1]
            matched_node_id = generalized_instance[pattern_node_id_with_wildcard]
            if attribute_name_with_wildcard not in G.get_node_attrs(matched_node_id):
                continue
            wildcard_value = G.get_node_attrs(matched_node_id)[attribute_name_with_wildcard]
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
                matched_node_id = generalized_instance[pattern_node_id_with_wildcard]
                node_attrs = G.get_node_attrs(matched_node_id)
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
    #StatCollector.getStatCollector().append_rule_data({'wildcard rules': len(rules)})
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
        instances.extend(G.find_matching_optimized(pattern, subgraph))
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
    instances_found = 0
    for rule in rules:
        pattern = rule.lhs
        instances = find_matching_optimised(G, pattern)
        #instances = G.find_matching(pattern)
        if instances:
            instances_found += len(instances)
            # print(instances)
            for instance in instances:
                G.rewrite(rule, instance)
    #StatCollector.getStatCollector().append_rule_data({'instances': instances_found})
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


def propagate(G: NXGraph, node_id):
    visited = set()
    to_visit = set()
    to_visit.add(node_id)
    while len(to_visit) > 0:
        visiting = to_visit.pop()
        visited.add(visiting)
        for neighbour in G.ancestors(visiting).union(G.descendants(visiting)):
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

    # print(instances)
    output_variables = list(set([instance[1] for instance in instances]))
    identifiers = list(set([instance[2] for instance in instances]))
    priorities = {}
    for node in output_variables + identifiers:
        cloud_ids = propagate(G, node)
        priorities[node] = min(cloud_ids)
    # print(priorities)
    new_instances = list()
    for index, identifier in enumerate(identifiers):
        child = None
        for instance in instances:
            if instance[2] == identifier:
                child = instance[3]
                break
        ### If child node text includes identifier node text in the following pattern '.TEXT' then we assume
        ### that this identifier is used as a attribute and there is no need to connect it to output variale
        if child:
            if 'text' in G.get_node_attrs(child).keys():
                if f'.{next(iter(G.get_node_attrs(identifier)["text"]))}' in next(iter(G.get_node_attrs(child)['text'])):
                    continue
        ###
        new_instance = {}
        # find all output variables that have lower priority than current identifier
        # AND represent the same variable
        lover_ovs = [ov for ov in output_variables if
                     priorities[ov] < priorities[identifier] and G.get_node_attrs(ov)['text'] ==
                     G.get_node_attrs(identifier)['text']]
        if (len(lover_ovs) < 1):
            print('SUS')
            continue
        ov_with_highest_prio = lover_ovs[0]
        for ov in lover_ovs:
            if priorities[ov] > priorities[ov_with_highest_prio]:
                ov_with_highest_prio = ov
        # OV with the highest priority is our OV
        old_instance_identifier_output = [instance for instance in instances if instance[2] == identifier][0][3]
        new_instance[1] = ov_with_highest_prio
        new_instance[2] = identifier
        new_instance[3] = old_instance_identifier_output
        new_instances.append(new_instance)
    # print(new_instances)

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

def deconstruct_forest_into_trees(G:NXGraph):
    trees = list()
    visited = set()
    for node in G.nodes():
        if node not in visited:
            same_tree_nodes = propagate(G, node)
            visited.update(same_tree_nodes)
            trees.append(G.subgraph(same_tree_nodes))
    return trees

def apply_rules_to_tree(tree, rules):
    for rule in rules:
        rule_start = time.time()
        tree = apply_rule(tree, rule[0])
        if len(tree.nodes(False)) == 0:
            break
        # if counter in []:
        #   utils.draw_graph(G, title=f'After rule {counter}')
        rule_end = time.time()
        # print(f'#{counter} {round(rule_end - rule_start, 5)}')
    return tree

def process_trees_concurrently(trees, rules):
    unconnected_rule = list()
    for counter, rule in enumerate(rules):
        pattern = Rule.from_json(read_rule_from_string(rule[0])).lhs
        if not set(pattern.nodes()) == set(propagate(pattern, pattern.nodes(True)[0][0])):
            unconnected_rule.append(rule)
        if len(unconnected_rule) > 0:
            raise Exception(f'Unconnected rule, can not process concurrently. Rule:{rule}')
        new_trees = None
    with Pool(processes=6) as pool:
        new_trees = pool.map(partial(apply_rules_to_tree, rules=rules), trees)
        #new_trees = pool.map(apply_rules_to_tree, map(lambda x: (x, rules) ,trees))
    new_trees = [tree for tree in new_trees if not len(tree.nodes(False)) == 0]
    return new_trees

def concatenate_two_graphs(G1:NXGraph, G2:NXGraph):
    G3 = NXGraph()
    G3.add_nodes_from(G1.nodes(True))
    G3.add_edges_from(G1.edges(True))
    G3.add_nodes_from(G2.nodes(True))
    G3.add_edges_from(G2.edges(True))
    return G3

def transform_graph(G: NXGraph, language, language_specific_hook: LanguageHook):
    """
    Applies rules from the rule base and further transformations to the given graph.

    :param G: an NXGraph object
    :return: graph in a json format
    """
    start_nodes_amount = len(G.nodes())
    pipeline = TransformationPipeline(language)
    start_iner = time.time()

    # connect to db
    db_path = os.path.join(os.path.dirname(__file__), "../knowledge_base.db")
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    flip_timer_start = time.time()
    # initial graph transformation
    flip_tree(G)
    #print_graph(G)
    #utils.draw_graph(G)
    flip_timer_end = time.time()

    # language_specific_hook
    if language_specific_hook:
        language_specific_hook.pre_hooks(G)

    # apply rules from rule base one by one
    rules = get_rules_from_db(cursor)
    rules_to_skip = []

    new_G = G.copy(G)
    new_G.remove_node(0)
    trees = deconstruct_forest_into_trees(new_G)
    rule_start = time.time()
    result = process_trees_concurrently(trees, rules)
    new_G:NXGraph = result[0]
    for tree in result[1:]:
        new_G = concatenate_two_graphs(tree, new_G)
    rule_end = time.time()
    print('concurrent result :', rule_end - rule_start)
    rules_timer_start = time.time()
    for counter, rule in enumerate(rules, 1):
        if counter in rules_to_skip:
            continue
        stats = StatCollector.getStatCollector()
        stats.new_rule()
        stats.append_rule_data({'rule id': rule[1], 'rule name': rule[2], 'rule type': rule[3]})
        rule_start = time.time()
        json_rule = read_rule_from_string(rule[0])
        G = apply_rule(G, rule[0])
        #if counter in []:
         #   utils.draw_graph(G, title=f'After rule {counter}')
        rule_end = time.time()
        stats.append_rule_data({'time': round(rule_end - rule_start, 5)})
        #print(f'#{counter} {round(rule_end - rule_start, 5)}')
        stats.store_rule_data()
    rules_timer_end = time.time()
    print('unconcurrent result :', rules_timer_end - rules_timer_start)
    #utils.draw_graph(G, title='After rules')


    pipeline_start = time.time()
    establish_connections(G)
    pipeline_end = time.time()
    # test_func(G)

    if language_specific_hook:
        language_specific_hook.post_hooks(G)

    kb_lookup_start = time.time()
    pipeline.knowledge_base_lookup(G)
    kb_lookup_end = time.time()

    graph_dict = nxgraph_to_json(G)

    pseudo_graph = utils.json_to_nxgraph(graph_dict)

    end_iner = time.time()

    nodes_end_amount = len(G.nodes())
    if False:
        print(f'nodes start: {start_nodes_amount} | '
              f'total: {round(end_iner - start_iner, 2)} | '
              f'flip: {round(flip_timer_end - flip_timer_start, 5)} | '
              f'rules: {round(rules_timer_end - rules_timer_start, 5)} | '
              f'kb_lookup: {round(kb_lookup_end - kb_lookup_start, 5)} | '
              f'pipeline: {round(pipeline_end - pipeline_start, 5)} | '
              f'nodes end: {nodes_end_amount}')
    script_stats = {'nodes at start': start_nodes_amount,
                    'total time': round(end_iner - start_iner, 2),
                    'rules time': round(rules_timer_end - rules_timer_start, 5),
                    'kb_lookup time': round(kb_lookup_end - kb_lookup_start, 5),
                    'pipeline time': round(pipeline_end - pipeline_start, 5),
                    'nodes at end': nodes_end_amount}
    stats = StatCollector.getStatCollector()
    stats.append_script_data(script_stats)

    #utils.draw_graph(G)
    #print_graph(G)
    connection.close()
    #print(len(G.nodes()), len(G.edges()), len(G.nodes())/len(G.edges()))
    return graph_dict


if __name__ == "__main__":
    for i in [17]:
        utils.draw_rule(i, RuleExtractor())
    pass
