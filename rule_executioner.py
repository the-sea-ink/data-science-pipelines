import sqlite3
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


def identify_inputs_outputs_in_assignment(G: NXGraph):
    """
    Identify inputs and outputs in an assignment in a form a = b.

    :param G:
    """
    pattern = NXGraph()
    pattern.add_node(1, {'type': 'identifier'})
    pattern.add_node(2, {'type': 'assignment'})
    pattern.add_node(3, {'type': 'identifier'})
    pattern.add_edge(1, 2)
    pattern.add_edge(3, 2)
    instances = G.find_matching(pattern)
    if instances:
        for instance in instances:
            if instance[1] < instance[3]:
                G.remove_edge(instance[1], instance[2])
                G.add_edge(instance[2], instance[1])
                attrs_output_variable = G.get_node(instance[1])
                attrs_output_variable["type"] = "output_variable"
                attrs_assignment = G.get_node(instance[2])
                attrs_assignment["type"] = "variable_assignment"
                attrs_input_variable = G.get_node(instance[3])
                attrs_input_variable["type"] = "input_variable"
                G.update_node_attrs(instance[1], attrs_output_variable)
                G.update_node_attrs(instance[2], attrs_assignment)
                G.update_node_attrs(instance[3], attrs_input_variable)
    return


def save_identifier_into_keyword_argument(G: NXGraph):
    """
    Saves "identifier" text into "keyword_argument" node as "identifier"
    attribute.

    :param G: an NXGraph object
    """
    pattern = NXGraph()
    pattern.add_node(1, {'type': 'identifier'})
    pattern.add_node(2, {'type': 'keyword_argument'})
    pattern.add_edge(1, 2)
    instances = G.find_matching(pattern)
    if instances:
        for instance in instances:
            attrs = G.get_node_attrs(instance[1])
            G.add_node_attrs(instance[2], {"identifier": attrs["text"]})
    return


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

    instances = []

    if utils.pattern_connected(pattern):
        # get subgraphs
        subgraphs = utils.get_ascendant_subgraphs_by_pattern(G, pattern)
        for subgraph in subgraphs:
            instances.extend(G.find_matching(pattern, subgraph))
    else:
        instances = G.find_matching(pattern)

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

    instances = []

    if utils.pattern_connected(pattern):
        # get subgraphs
        subgraphs = utils.get_ascendant_subgraphs_by_pattern(G, pattern)
        for subgraph in subgraphs:
            instances.extend(G.find_matching(pattern, subgraph))
    else:
        instances = G.find_matching(pattern)

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

    Finds instances of imported modules "dotted_name" -> "import_statement"
    and returns them as a list of strings.

    :param G: A NXGraph object
    :return: A list of strings representing the imported modules
    """

    pattern = NXGraph()
    pattern.add_node(1, {'type': 'dotted_name'})
    pattern.add_node(2, {'type': 'import_statement'})
    pattern.add_edge(1, 2)
    instances = []

    if utils.pattern_connected(pattern):
        # get subgraphs
        subgraphs = utils.get_ascendant_subgraphs_by_pattern(G, pattern)
        for subgraph in subgraphs:
            instances.extend(G.find_matching(pattern, subgraph))
    else:
        instances = G.find_matching(pattern)

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
    instances.extend(G.find_matching(pattern))

    pattern = NXGraph()
    pattern.add_node(1, {'type': 'import_from_statement'})
    instances.extend(G.find_matching(pattern))
    if instances:
        for instance in instances:
            nodes = utils.get_ancestors_nodes(G, instance[1])
            for node in nodes:
                G.remove_node(node)
    return

def connect_parents_children_drop_node(G: NXGraph, attr: str):
    """
    Find instances of the node we want to remove, connect its parents and children,
    remove node.

    :param G: a NXGraph object
    :param attr: attribute of the node that we want to remove
    """
    # connect parents and children of slice, remove node by type
    pattern = NXGraph()
    pattern.add_node(1, {'type': attr})
    instances = G.find_matching(pattern)
    for instance in instances:
        node_id = instance[1]
        parents = G.predecessors(node_id)
        children = G.successors(node_id)
        for child in children:
            for parent in parents:
                G.add_edge(parent, child)
        G.remove_node(node_id)


def add_attributes_from_import_aliases(G: NXGraph, aliases_dict: dict, cursor):
    """
    Looks for instances of nodes with the attribute "identifier" that match a key
    in the aliases_dict. If such nodes are found, the function removes the "identifier"
    attribute and adds the "module" attribute with the value of the corresponding value
    in the aliases_dict. The function also adds the "full_function_call" attribute
    by concatenating the value of the aliases_dict with the text attribute of the node,
    if the key appears in the text attribute. The function also attempts to retrieve a
    knowledge base entry for the function and adds the description of that entry as an
    attribute to the node, if it is found.

    :param G: a NXGraph object
    :param alieses_dict: A dictionary of import aliases, where keys are the short identifiers
     and values are the full function names.
    :param cursor: A cursor object to access a database, which is used to retrieve a
    knowledge base entry for the functions
    """
    for key in aliases_dict:
        pattern = NXGraph()
        pattern.add_node(1, {'identifier': key})
        instances = (G.find_matching(pattern))
        if instances:
            for instance in instances:
                # remove short identifier from identifiers list
                node_id = instance[1]
                node_attrs = G.get_node(node_id)
                G.remove_node_attrs(node_id, {'identifier': key})
                # add "module" attribute and put full function name there
                module_name = aliases_dict[key].decode("utf-8")
                G.add_node_attrs(node_id, {"module": module_name})
                # add full function call to the node
                for value in node_attrs["text"]:
                    node_text = value.decode("utf-8")
                    short_name = key.decode("utf-8")
                    long_name = aliases_dict[key].decode("utf-8")
                    if short_name in node_text:
                        full_name = long_name + node_text[len(short_name):]
                        G.add_node_attrs(node_id, {"full_function_call": full_name})
                # get knowledge base entry
                kb_function = Function.parse_from_db(cursor, module_name, full_name)
                if kb_function != -1:
                    G.add_node_attrs(node_id, {"description": kb_function.description})


def add_attributes_from_functions_dict(G: NXGraph, functions_dict: dict, cursor):
    for key in functions_dict:
        pattern = NXGraph()
        pattern.add_node(1, {'text': key})
        instances = (G.find_matching(pattern))
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
            kb_function = Function.parse_from_db(cursor, module_name, full_name)
            if kb_function != -1:
                G.add_node_attrs(node_id, {"description": kb_function.description})


def add_attributes_from_module_list(G: NXGraph, imported_modules: list, cursor):
    for module in imported_modules:
        for module_name in module:
            pattern = NXGraph()
            pattern.add_node(1, {'identifier': module_name})
            instances = (G.find_matching(pattern))
            for instance in instances:
                # add "module" attribute and put full function name there
                node_id = instance[1]
                function_call = G.get_node(node_id)["text"]
                for function_name in function_call:
                    G.add_node_attrs(node_id, {"module": module_name.decode("utf-8")})
                    # add full function call
                    G.add_node_attrs(node_id, {"full_function_call": function_name.decode("utf-8")})
                    kb_function = Function.parse_from_db(cursor, module_name.decode("utf-8"),
                                                         function_name.decode("utf-8"))
                    if kb_function != -1:
                        G.add_node_attrs(node_id, {"description": kb_function.description})


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


def process_wildcard_attributes(rule:NXGraph, G:NXGraph, rule_string):
    pattern = rule.lhs
    wildcards = {}

    for node, attrs in pattern.nodes(True):
        for attribute in attrs:
            for elem in attrs[attribute]:
                if "%unknown_value" in elem:
                    #create a list of wildcard node occurrences
                    if elem not in wildcards.keys():
                        wildcards[elem] = []
                    wildcards[elem].append((node, attribute))

    generalized_pattern = pattern.copy(pattern)
    if len(wildcards) == 0:
        return [rule]
    for wildcard, wildcard_occurrances in wildcards.items():
        for occurance in wildcard_occurrances:
            generalized_pattern.remove_node_attrs(occurance[0],
                                                {occurance[1]:wildcard})
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
            shared_wildcard_values = {k: rule_answer[k] for k in rule_answer if k in wildcard_matches and rule_answer[k] == wildcard_matches[k]}
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


def find_matching_optimised(G, pattern):
    instances = []
    if utils.pattern_connected(pattern):
        # get subgraphs for faster instance finding
        subgraphs = utils.get_ascendant_subgraphs_by_pattern(G, pattern)
        for subgraph in subgraphs:
            instances.extend(G.find_matching(pattern, subgraph))
    else:
        instances = G.find_matching(pattern)
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
            for instance in instances:
                G.rewrite(rule, instance)

    return G


def transform_graph(G: NXGraph):
    """
    Applies rules from the rule base and further transformations to the given graph.

    :param G: an NXGraph object
    :return: graph in a json format
    """

    start_iner = time.time()

    # connect to db
    connection = sqlite3.connect("knowledge_base.db")
    cursor = connection.cursor()

    # initial graph transformation
    flip_tree(G)
    utils.print_graph(G)

    # transform and save import statements, remove them from tree
    aliases_dict = save_import_aliases(G)
    functions_dict = save_imported_functions(G)
    imported_modules = save_imported_modules(G)
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
        if counter == 5:
            print("yo")
            #utils.draw_rule()
        G = apply_rule(G, rule[0])
        print_graph(G)
        end_iner = time.time()
        # print(f'line {counter} done in {end_iner - start_iner}')
    end_outer = time.time()
    # print(f'apply rule  done in {end_outer - start_outer}')
    start_iner = time.time()


    # add knowledge base enrichment to functions that are present there
    add_attributes_from_import_aliases(G, aliases_dict, cursor)
    add_attributes_from_functions_dict(G, functions_dict, cursor)
    add_attributes_from_module_list(G, imported_modules, cursor)
    add_labels(G)

    end_iner = time.time()
    print(f'post transformations done in {end_iner - start_iner}')
    print_graph(G)
    graph_dict = convert_graph_to_json(G)
    connection.close()
    return graph_dict
