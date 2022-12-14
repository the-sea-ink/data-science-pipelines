import sqlite3
from regraph import NXGraph, Rule, FiniteSet, plot_graph
import json
import ast
import time
import utils
from models.Function import Function


def flip_tree(G: NXGraph):
    root_node = utils.get_root_node_id(G)
    flip_node(G, root_node)
    return


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


def adjust_call(G: NXGraph):
    # add identifier attribute to call node, remove identifier node
    pattern = NXGraph()
    pattern.add_node(1, {'type': 'identifier'})
    pattern.add_node(2, {'type': 'call'})
    pattern.add_edge(1, 2)

    instances = []
    instances.extend(G.find_matching(pattern))

    for instance in instances:
        identifier_id = instance[1]
        call_id = instance[2]
        identifier_attrs = G.get_node(identifier_id)
        identifier_text = identifier_attrs["text"]
        G.update_node_attrs(call_id, {"type": "call", "text": identifier_text})
        G.remove_node(identifier_id)
    return


def adjust_attributes(G: NXGraph):
    pattern = NXGraph()
    pattern.add_node(1, {'type': 'attribute'})
    pattern.add_node(2, {'type': 'call'})
    pattern.add_edge(1, 2)
    instances = G.find_matching(pattern)
    for instance in instances:
        attr_id = instance[1]
        call_id = instance[2]
        attr_attrs = G.get_node(attr_id)
        attr_text = attr_attrs["text"]
        G.update_node_attrs(call_id, {"type": "call", "text": attr_text})
        parents = G.predecessors(attr_id)
        children = G.successors(attr_id)
        for child in children:
            for parent in parents:
                G.add_edge(parent, child)
        G.remove_node(attr_id)
    return


def adjust_arguments(G: NXGraph):
    # connect parents and children of argument list, remove argument list node
    pattern = NXGraph()
    pattern.add_node(1, {'type': 'argument_list'})
    instances = G.find_matching(pattern)
    for instance in instances:
        argument_id = instance[1]
        parents = G.predecessors(argument_id)
        children = G.successors(argument_id)
        for child in children:
            for parent in parents:
                G.add_edge(parent, child)
                parent_node = G.get_node(parent)
                # if it is an identifier, rename to input variable
                for elem in parent_node["type"]:
                    if elem == "identifier":
                        G.update_node_attrs(parent, {"text": parent_node["text"], "type": "input_variable"})
        G.remove_node(argument_id)
    return


def process_assignment(G: NXGraph):
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


def save_import_aliases(G: NXGraph):
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
        subgraphs = get_ascendant_subgraphs_by_pattern(G, pattern)
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


def remove_import_statements(G: NXGraph):
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


def cleanup(G):
    # redundant parents
    redundancy_list = [
        "expression_statement",
        "assignment",
        "pattern_list",
        "module",
        "slice"
    ]
    for redundancy in redundancy_list:
        redundancy_pattern = utils.create_pattern("node_id", "type", redundancy)
        instances = G.find_matching(redundancy_pattern)
        for instance in instances:
            utils.remove_nodes(G, [instance["node_id"]])
    # keyword argument children
    keyword_parents = [
        "string",
        "integer",
        "float",
        "true",
        "false"
    ]
    for parent in keyword_parents:
        keyword_pattern = NXGraph()
        keyword_pattern.add_node(1, {'type': parent})
        keyword_pattern.add_node(2, {'type': 'keyword_argument'})
        keyword_pattern.add_edge(1, 2)
        keyword_instances = G.find_matching(keyword_pattern)
        for keyword_instance in keyword_instances:
            G.remove_node(keyword_instance[1])

    return G


def compare_outputs_inputs(G: NXGraph, output_instances, input_instances, nodes_to_remove):
    # check if same names, remove input node, update output attriute
    for output_instance in output_instances:
        output_identifier = output_instance[2]
        output_caller_function = output_instance[1]
        output_node = G.get_node(output_identifier)
        for input_instance in input_instances:
            input_identifier = input_instance[1]
            input_caller_function = input_instance[2]
            input_node = G.get_node(input_identifier)
            # if same, remove nodes and add edge
            if output_node['text'] == input_node['text']:
                # if output_identifier not in nodes_to_remove:
                # nodes_to_remove.append(output_identifier)
                if input_identifier not in nodes_to_remove:
                    nodes_to_remove.append(input_identifier)
                G.update_node_attrs(output_identifier, {"type": "passable_data", "text": output_node['text']})
                # add edge between caller functions
                # if exists, add further attribute
                G.add_edge(output_identifier, input_caller_function)

                continue

    return G, output_instances, input_instances, nodes_to_remove


def connect_variables(G):
    """
    1. search for outputs
    2. search for inputs
    3. check if they have the same text values
    4. if yes, remove both, make edge between parent of 1 and child of 2
    5. save rest of identifiers as attribute of their parent or child respectfully
    """

    # TODO eventually optimization needed, since node 1 has no attrs
    # if an identifier node is a child of a caller function, it is an output value of a function
    output_pattern = NXGraph()
    output_pattern.add_node(1)
    output_pattern.add_node(2, {'type': 'output_variable'})
    output_pattern.add_edge(1, 2)
    output_instances = G.find_matching(output_pattern)

    # if an identifier node is a parent to any node, it is an input value into that function
    # check in known inputs
    input_pattern = NXGraph()
    input_pattern.add_node(1, {'type': 'input_variable'})
    input_pattern.add_node(2)
    input_pattern.add_edge(1, 2)
    input_instances = G.find_matching(input_pattern)

    # print(output_instances)
    nodes_to_remove = []
    # print(type(output_instances))

    G, output_instances, input_instances, nodes_to_remove = compare_outputs_inputs(G, output_instances,
                                                                                   input_instances, nodes_to_remove)
    # go though leftover inputs, save them into their
    # belonging functions as attribute
    for input_instance in input_instances:

        input_id = input_instance[1]
        # if input_id in nodes_to_remove:
        # continue
        children = G.successors(input_id)
        input_node = G.successors(input_id)
        # save attr in child
        input_node = G.get_node(input_id)
        child_id = list(children)[0]
        child_node = G.get_node(child_id)
        if "input_variable" in child_node:
            for elem in input_node["text"]:
                child_node["input_variable"].add(elem)
        else:
            child_node["input_variable"] = input_node["text"]
        G.update_node_attrs(child_id, child_node)
        if input_id not in nodes_to_remove:
            nodes_to_remove.append(input_id)

    # check identifiers fpr potential inputs
    input_pattern = NXGraph()
    input_pattern.add_node(1, {'type': 'identifier'})
    input_pattern.add_node(2)
    input_pattern.add_edge(1, 2)

    input_instances = G.find_matching(input_pattern)
    G, output_instances, input_instances, nodes_to_remove = compare_outputs_inputs(G, output_instances,
                                                                                   input_instances, nodes_to_remove)
    for input_instance in input_instances:
        input_id = input_instance[1]
        children = G.successors(input_id)
        # save attr in child
        input_node = G.get_node(input_id)
        child_id = list(children)[0]
        child_node = G.get_node(child_id)
        # if we met this node before, it is an object or a variable
        if input_id in nodes_to_remove:
            child_node["variable"] = input_node["text"]
        else:
            if "identifier" in child_node:
                for elem in input_node["text"]:
                    child_node["identifier"].add(elem)
            else:
                child_node["identifier"] = input_node["text"]
        G.update_node_attrs(child_id, child_node)
        if input_id not in nodes_to_remove:
            nodes_to_remove.append(input_id)

    # go through leftover outputs, save them into their
    # belonging functions as attribute
    for output_instance in output_instances:
        output_id = output_instance[2]
        # if output_id in nodes_to_remove:
        # continue
        parents = G.predecessors(output_id)
        # save attribute in parent
        output_node = G.get_node(output_id)
        parent_id = list(parents)[0]
        parent_node = G.get_node(parent_id)
        if "output_variable" in parent_node:
            for elem in output_node["text"]:
                parent_node["output_variable"].add(elem)
        else:
            parent_node["output_variable"] = output_node["text"]
        G.update_node_attrs(parent_id, parent_node)
        # if output_id not in nodes_to_remove:
        # nodes_to_remove.append(output_id)
    for id in nodes_to_remove:
        G.remove_node(id)
    return


def adjust_subscript(G: NXGraph):
    # connect parents and children of subscript, remove subscript node
    pattern = NXGraph()
    pattern.add_node(1, {'type': 'subscript'})
    instances = G.find_matching(pattern)
    for instance in instances:
        node_id = instance[1]
        parents = G.predecessors(node_id)
        children = G.successors(node_id)
        for child in children:
            for parent in parents:
                G.add_edge(parent, child)
        G.remove_node(node_id)
    return


def adjust_slice(G: NXGraph):
    # connect parents and children of slice, remove slice node
    pattern = NXGraph()
    pattern.add_node(1, {'type': 'slice'})
    instances = G.find_matching(pattern)
    for instance in instances:
        node_id = instance[1]
        parents = G.predecessors(node_id)
        children = G.successors(node_id)
        for child in children:
            for parent in parents:
                G.add_edge(parent, child)
        G.remove_node(node_id)
    return


def add_module_attributes(G: NXGraph, alieses_dict: dict, cursor):
    for key in alieses_dict:
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
                module_name = alieses_dict[key].decode("utf-8")
                G.add_node_attrs(node_id, {"module": module_name})
                # add full function call to the node
                for value in node_attrs["text"]:
                    node_text = value.decode("utf-8")
                    short_name = key.decode("utf-8")
                    long_name = alieses_dict[key].decode("utf-8")
                    if short_name in node_text:
                        full_name = long_name + node_text[len(short_name):]
                        G.add_node_attrs(node_id, {"full_function_call": full_name})
                # get knowledge base entry
                kb_function = Function.parse_from_db(cursor, module_name, full_name)
                G.add_node_attrs(node_id, {"description": kb_function.description})

    return


def add_labels(G: NXGraph):
    nodes = G.nodes()
    for node_id in nodes:
        node = G.get_node(node_id)
        node_text = node["text"]
        G.add_node_attrs(node_id, {"label": node_text})
    return


def execute_rule(G, pattern, rule):
    pattern_instances = G.find_matching(pattern)
    if pattern_instances:
        for instance in pattern_instances:
            G.rewrite(rule, instance)
    return


def read_rule_from_line(line):
    string = line.rstrip()
    rule = ast.literal_eval(string)
    return rule


def get_ascendant_subgraphs_by_pattern(G: NXGraph, pattern: NXGraph):
    anti_root_id = [node for node in pattern.nodes() if len(pattern.descendants(node)) == 0][0]
    anti_root_attrs = pattern.get_node(anti_root_id)
    # find all instances of root in graph
    root_pattern = NXGraph()
    root_pattern.add_node(anti_root_id, anti_root_attrs)
    instances = G.find_matching(root_pattern)
    subgraphs = []
    if instances:
        for instance in instances:
            subgraphs.append(utils.get_ancestors_nodes(G, list(instance.values())[0]))
    return subgraphs


def apply_rule(G, json_rule):
    rule = Rule.from_json(json_rule)
    pattern = rule.lhs

    instances = []

    if utils.pattern_connected(pattern):
        # get subgraphs
        subgraphs = get_ascendant_subgraphs_by_pattern(G, pattern)
        for subgraph in subgraphs:
            instances.extend(G.find_matching(pattern, subgraph))
    else:
        instances = G.find_matching(pattern)

    # instances = G.find_matching(pattern)
    if instances:
        # print(json_rule)
        # print_graph(G)
        for instance in instances:
            # print(type(instances))
            G.rewrite(rule, instance)

    return G


def jsonify_finite_set(param):
    if len(param.to_json()["data"]) > 1:
        result_list = list()
        for element in param.to_json()["data"]:
            if isinstance(element, (bytes, bytearray)):
                result_list.append(element.decode("utf-8"))
            else:
                result_list.append(element)
        return result_list
    data = param.to_json()["data"][0]
    if isinstance(data, (bytes, bytearray)):
        data = data.decode("utf-8")
    return data



def convert_graph_to_json(G):
    graph_dict = {"nodes": [], "edges": []}
    for n, attrs in G.nodes(data=True):
        if str(attrs["type"]) == "{'input'}":
            metadata = {"id": str(n), "type": "input", "targetPosition": "top", "position": {"x": 0, "y": 0},
                        "data": {}}
        else:
            metadata = {"id": str(n), "type": "default", "targetPosition": "top", "position": {"x": 0, "y": 0},
                        "data": {}}
        # node_attrs = {}
        node_raw_attrs = G.get_node(n)
        for key in node_raw_attrs:
            metadata["data"].update({key: jsonify_finite_set(node_raw_attrs[key])})

        # node_attrs.update(G.get_node(n))
        graph_data = {}
        graph_dict["nodes"].append(metadata)
        # graph_dict["nodes"].append(graph_data)
    i = 1
    for s, t, attrs in G.edges(data=True):
        edge_id = "edge-" + str(i)
        edge_attrs = {"id": edge_id, "source": str(s), "target": str(t), 'type': 'smoothstep'}
        graph_dict["edges"].append(edge_attrs)
        i += 1
    with open('graph.json', 'w') as fp:
        json.dump(graph_dict, fp, indent=4)
    return graph_dict


def transform_graph(G):
    connection = sqlite3.connect("knowledge_base.db")
    cursor = connection.cursor()
    flip_tree(G)
    utils.print_graph(G)
    aliases_dict = save_import_aliases(G)
    remove_import_statements(G)
    process_assignment(G)
    adjust_call(G)
    adjust_attributes(G)
    adjust_arguments(G)


    # print_graph(G)

    start_outer = time.time()
    with open("knowledge_base/rule_base.txt") as file:
        for counter, line in enumerate(file, 1):
            start_iner = time.time()
            json_rule = read_rule_from_line(line)
            # print_graph(G)
            # print(f'Applying rule #{counter}')
            G = apply_rule(G, json_rule)
            # if counter == 21:
            # print_graph(G)
            end_iner = time.time()
            # print(f'line {counter} done in {end_iner - start_iner}')
    end_outer = time.time()
    # print(f'apply rule  done in {end_outer - start_outer}')

    adjust_subscript(G)
    adjust_slice(G)
    cleanup(G)
    connect_variables(G)
    add_module_attributes(G, aliases_dict, cursor)
    add_labels(G)

    utils.print_graph(G)

    # create_subgraph(G, 1)

    graph_dict = convert_graph_to_json(G)
    # print(graph_dict)
    return graph_dict