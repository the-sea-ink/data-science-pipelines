import sqlite3

from networkx.algorithms.isomorphism import GraphMatcher
from regraph import NXGraph, Rule, FiniteSet, plot_graph
import time
import utils
from utils import draw_graph, print_graph, read_rule_from_string, convert_graph_to_json_new_frontend, \
    convert_graph_to_json
from models.Function import Function
from rule_manager import get_rules_from_db

STR_NODE_ID = "node_id"
STR_ATTR_NAME = "attr_name"
STR_ATTR_VALUE = "attr_value"


class TransformationPipeline():

    def __init__(self, language):
        self.connection = sqlite3.connect("knowledge_base.db")
        self.cursor = self.connection.cursor()
        self.language = language

    def pre_hooks(self, G: NXGraph):
        if self.language == "python":
            self.aliases_dict = save_import_aliases(G)
            self.functions_dict = save_imported_functions(G)
            self.imported_modules = save_imported_modules(G)
        return G

    def post_hooks(self, G: NXGraph):
        # add knowledge base enrichment to functions that are present there
        if self.language == "python":
            add_attributes_from_import_aliases(G, self.aliases_dict)
            add_attributes_from_functions_dict(G, self.functions_dict, self.cursor)
            add_attributes_from_module_list(G, self.imported_modules, self.cursor)
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


def save_import_aliases(G: NXGraph):
    """
    Handles 'import numpy as np'.

    :param G: A NXGraph object
    """
    # create pattern for aliases
    pattern = NXGraph()
    pattern.add_node(1, {'type': 'aliased_import'})
    pattern.add_node(2, {'type': 'dotted_name'})
    pattern.add_node(3, {'type': 'identifier'})
    pattern.add_edge(2, 1)
    pattern.add_edge(3, 1)

    instances = find_matching_optimised(G, pattern)

    aliases_dict = {}

    # save all aliases
    for instance in instances:
        aliased_import_id = instance[1]
        dotted_name_id = instance[2]
        identifier_id = instance[3]

        dotted_name = G.get_node(dotted_name_id)
        identifier = G.get_node(identifier_id)
        for key, value in zip(identifier["text"], dotted_name["text"]):
            aliases_dict[key] = value

    for alias, module in aliases_dict.items():
        nodes_to_remove = [x for x in G.nodes(True) if next(iter(x[1]['text'])) == alias]
        for node in nodes_to_remove:
            G.remove_node(node[0])
    return aliases_dict


def save_imported_functions(G: NXGraph):
    """
    Handles "from numpy import function".

    :param G:
    :return:
    """
    pattern = NXGraph()
    pattern.add_node(1, {'type': 'dotted_name'})
    pattern.add_node(2, {'type': 'import_from_statement'})
    pattern.add_node(3, {'type': 'dotted_name'})
    pattern.add_edge(1, 2)
    pattern.add_edge(3, 2)

    instances = find_matching_optimised(G, pattern)

    functions_dict = {}
    if instances:
        for instance in instances:
            if instance[1] < instance[3]:
                module_name = G.get_node(instance[1])["text"]
                function_name = G.get_node(instance[3])["text"]
                for mod_name, func_name in zip(module_name, function_name):
                    functions_dict[func_name] = mod_name + "." + func_name
                    # print(functions_dict)
    return functions_dict


def save_imported_modules(G: NXGraph):
    """
    Handles "import module".

    Finds instances of imported scraped_modules "dotted_name" -> "import_statement"
    and returns them as a list of strings.

    :param G: A NXGraph object
    :return: A list of strings representing the imported scraped_modules
    """

    pattern = NXGraph()
    pattern.add_node(1, {'type': 'dotted_name'})
    pattern.add_node(2, {'type': 'import_statement'})
    pattern.add_edge(1, 2)
    instances = []

    instances = find_matching_optimised(G, pattern)

    imported_modules = []
    if instances:
        for instance in instances:
            imported_modules.append(G.get_node(instance[1])["text"])

    return imported_modules


def remove_import_statements(G: NXGraph):
    """
    Removes import statements from a given NXGraph object.
    It searches for both 'import_statement' and 'import_from_statement' nodes
    and removes them along with their ancestors nodes.

    Parameters:
    G (NXGraph): The NXGraph object containing the import statements to remove.

    Returns:
    None
    """
    instances = []
    pattern = NXGraph()
    pattern.add_node(1, {'type': 'import_statement'})
    instances.extend(find_matching_optimised(G, pattern))

    pattern = NXGraph()
    pattern.add_node(1, {'type': 'import_from_statement'})
    instances.extend(find_matching_optimised(G, pattern))
    if instances:
        for instance in instances:
            nodes = utils.get_ancestors_nodes(G, instance[1])
            for node in nodes:
                G.remove_node(node)
    return


def add_attributes_from_import_aliases(G: NXGraph, aliases_dict: dict):
    """
    :param G: a NXGraph object
    :param alieses_dict: A dictionary of import aliases, where keys are the short identifiers
     and values are the full function names.
    :param cursor: A cursor object to access a database, which is used to retrieve a
    knowledge base entry for the functions
    """
    for alias, module in aliases_dict.items():
        nodes_to_change = [x for x in G.nodes(True) if next(iter(x[1]['text'])).startswith(alias+'.')]
        for node in nodes_to_change:
            G.add_node_attrs(node[0], {"full_function_call": next(iter(node[1]['text'])).replace(alias, module, 1)})
            G.add_node_attrs(node[0], {"module": module})
            G.add_node_attrs(node[0], {"alias": alias})

                # get knowledge base entry
                #kb_function = Function.get_function_by_name_module_language(cursor, module_name, full_name)
                #if kb_function != -1:
                #    G.add_node_attrs(node_id, {"description": kb_function.description})


def add_attributes_from_functions_dict(G: NXGraph, functions_dict: dict, cursor):
    for key in functions_dict:
        pattern = NXGraph()
        pattern.add_node(1, {'text': key})
        instances = find_matching_optimised(G, pattern)
        for instance in instances:
            # add "module" attribute and put full function name there
            node_id = instance[1]
            index = functions_dict[key].find(".")
            module_name = functions_dict[key][:index]
            G.add_node_attrs(node_id, {"module": module_name})
            # add full function call to the node
            full_name = functions_dict[key]
            G.add_node_attrs(node_id, {"full_function_call": full_name})
            # get knowledge base entry
            #kb_function = Function.parse_from_db_by_name_and_module(cursor, module_name, full_name)
            #if kb_function != -1:
            #    G.add_node_attrs(node_id, {"description": kb_function.description})


def add_attributes_from_module_list(G: NXGraph, imported_modules: list, cursor):
    for module in imported_modules:
        for module_name in module:
            pattern = NXGraph()
            pattern.add_node(1, {'identifier': module_name})
            instances = find_matching_optimised(G, pattern)
            for instance in instances:
                # add "module" attribute and put full function name there
                node_id = instance[1]
                function_call = G.get_node(node_id)["text"]
                for function_name in function_call:
                    G.add_node_attrs(node_id, {"module": module_name})
                    # add full function call
                    G.add_node_attrs(node_id, {"full_function_call": function_name})
                    #kb_function = Function.parse_from_db_by_name_and_module(cursor, module_name.decode("utf-8"), function_name.decode("utf-8"))
                    #if kb_function != -1:
                    #    G.add_node_attrs(node_id, {"description": kb_function.description})


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
    if utils.pattern_connected(pattern):
        instances = find_connected_graph(G, pattern)

    else:
        instances = G.find_matching(pattern)
    equal = True
    for opt in optimited_instances:
        if opt not in instances:
            equal = False
            break
    if not equal:
        raise Exception("RESULTS ARE NOT EQUAL")

    return instances


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


def knowledge_base_lookup(G: NXGraph):
    instances = []
    pattern = NXGraph()
    pattern.add_node(1, {'type': 'call'})
    instances.extend(find_matching_optimised(G, pattern))
    print("yo")
    #function = Function.get_function_by_name_module_language("", "", "", "")
    pass


def transform_graph(G: NXGraph, language):
    """
    Applies rules from the rule base and further transformations to the given graph.

    :param G: an NXGraph object
    :return: graph in a json format
    """
    pipeline = TransformationPipeline(language)
    start_iner = time.time()

    # connect to db
    connection = sqlite3.connect("knowledge_base.db")
    cursor = connection.cursor()

    # initial graph transformation
    flip_tree(G)
    utils.print_graph(G)

    pipeline.pre_hooks(G)
    remove_import_statements(G)

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
        if end_iner - start_iner > 3:
            utils.draw_rule(counter)
        # print(f'line {counter} done in {end_iner - start_iner}')
    end_outer = time.time()
    # print(f'apply rule  done in {end_outer - start_outer}')
    start_iner = time.time()

    pipeline.post_hooks(G)
    knowledge_base_lookup(G)

    end_iner = time.time()
    print(f'post transformations done in {end_iner - start_iner}')
    print_graph(G)
    draw_graph(G)
    graph_dict = convert_graph_to_json(G)
    connection.close()
    return graph_dict


if __name__ == "__main__":
    utils.draw_rule(15)
    pass
