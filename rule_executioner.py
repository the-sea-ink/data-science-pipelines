import csv
from regraph import NXGraph, Rule, FiniteSet, plot_graph
import json
import ast
import time
import matplotlib.pyplot as plt
import networkx as nx
from regraph.backends.networkx.plotting import plot_rule
import utils


def remove_descendants_from_instances(G, node_type, instances):
    removed_nodes = []
    for ins in instances:
        node_id = ins[node_type]
        # handling nested function calls;
        # checking if we deleted a subgraph of a nested function yet
        if node_id not in removed_nodes:
            desc = G.descendants(node_id)
            for id in list(desc):
                G.remove_node(id)
                removed_nodes.append(id)
    return removed_nodes


def remove_descendants_from_node(G, node_id):
    removed_nodes = []
    children = G.descendants(node_id)
    for child in list(children):
        G.remove_node(child)
        removed_nodes.append(child)
    return removed_nodes


def remove_nodes(G, ids):
    for id in ids:
        G.remove_node(id)
    return


def save_imports(G, node_ids):
    import_dict = []
    for id in node_ids:
        node_attributes = G.get_node(id)
        import_dict.append(node_attributes)
    return import_dict


# gets the ids of all the nodes of a certain "type" in an instance of a graph
def get_ids(node_type, instances):
    ids = []
    for instance in instances:
        node_id = instance[node_type]
        ids.append(node_id)
    return ids


# creates a pattern to filter a graph based on "node type"
# attr_name -> name given to the variable used to identify this node type
# node_type -> the type of node that wants to be filtered
def create_pattern(id, attr_name, node_type):
    pattern = NXGraph()
    pattern.add_node(id, {attr_name: node_type})
    return pattern


##TODO restrict subgraph deepness
def get_ancestors_nodes(G: NXGraph, node_id):
    subg_nodes = list(G.ancestors(node_id))
    subg_nodes.append(node_id)
    return subg_nodes


def create_subgraph(G, node_id):
    subg_nodes = list(G.descendants(node_id))
    subg_nodes.append(node_id)
    subgraph = G.generate_subgraph(G, subg_nodes)
    return subgraph


def print_graph(G):
    # print clear view of all nodes and their edges
    print("List of nodes: ")
    for n, attrs in G.nodes(data=True):
        print("\t", n, attrs)
    print()
    print("List of edges: ")
    for s, t, attrs in G.edges(data=True):
        print("\t{}->{}".format(s, t), attrs)


def sort_instances(all_instances, last_node_type):
    """
    Sorts all the instances, by the index of the last node's type. Since the initial parsed tree is traversed using
    breadth-first-search, by sorting by the last index in the tree you are also sorting the indexes of all the other
    node's types.
    """
    return sorted(all_instances, key=lambda x: (x[last_node_type]))


def print_nodes(graph, node_ids):
    for id in node_ids:
        print(graph.get_node(id))


def trim(attribute):
    pos = attribute.find(".")
    attribute = attribute[pos + 1:]
    return attribute


def flip_the_table(G: NXGraph):
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

# TODO fix needed, failing example error_code_1
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


def process_assignment(G):
    # TODO add 2 identifiers
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
            nodes = get_ancestors_nodes(G, instance[1])
            for node in nodes:
                G.remove_node(node)
    return


def change_aliases_in_functions(G: NXGraph, aliases_dict):
    # TODO check for identifier -> node pattern, adjust display names
    return


def apply_pre_transformations(G):

    aliases_dict = save_import_aliases(G)

    remove_import_statements(G)
    adjust_call(G)
    adjust_attributes(G)
    adjust_arguments(G)
    return aliases_dict


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
        redundancy_pattern = create_pattern("node_id", "type", redundancy)
        instances = G.find_matching(redundancy_pattern)
        for instance in instances:
            remove_nodes(G, [instance["node_id"]])
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


def compare_outputs_inputs(G:NXGraph, output_instances, input_instances, nodes_to_remove):
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
                #if output_identifier not in nodes_to_remove:
                    #nodes_to_remove.append(output_identifier)
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
        #if output_id not in nodes_to_remove:
            #nodes_to_remove.append(output_id)
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

#  TODO redo algorithm into recursion
def adjust_attributes_2(G: NXGraph):
    instances = []

    pattern = NXGraph()
    #pattern.add_node(1, {'type': 'attribute'})
    #pattern.add_node(2, {'type': 'attribute'})
    #pattern.add_edge(2, 1)
    #instances.extend(G.find_matching(pattern))

    pattern = NXGraph()
    pattern.add_node(1, {'type': 'call'})
    pattern.add_node(2, {'type': 'attribute'})
    pattern.add_edge(2, 1)
    instances.extend(G.find_matching(pattern))

    for instance in instances:
        node_id_to_go = instance[2]
        node_id_to_stay = instance[1]
        parents = G.predecessors(node_id_to_go)
        children = G.successors(node_id_to_go)
        for child in children:
            for parent in parents:
                G.add_edge(parent, child)
        # remove type, append rest of the attrs to node to stay
        node_to_go = G.get_node(node_id_to_go)
        node_to_go.pop("type")
        node_to_stay = G.get_node(node_id_to_stay)
        node_to_stay.pop("text")
        for key in node_to_go.keys():
            if key in node_to_stay:
                for elem in node_to_go[key]:
                    node_to_stay[key].add(elem)
            else:
                G.add_node_attrs(node_id_to_stay, {key: node_to_go[key]})
        G.remove_node(node_id_to_go)
    return


def add_library_attribute(G: NXGraph, alieses_dict: dict):
    for key in alieses_dict:
        pattern = NXGraph()
        pattern.add_node(1, {'identifier': key})
        instances = (G.find_matching(pattern))
        for instance in instances:
            # remove short identifier from identifiers list
            node_id = instance[1]
            node_attrs = G.get_node(node_id)
            G.remove_node_attrs(node_id, {'identifier': key})
            # add "library" attribute and put full function name there
            G.add_node_attrs(node_id, {"library": alieses_dict[key]})
            # add full function call to the node
            for value in node_attrs["text"]:
                node_text = value.decode("utf-8")
                short_name = key.decode("utf-8")
                long_name = alieses_dict[key].decode("utf-8")
                if short_name in node_text:
                    full_name = long_name + node_text[len(short_name):]
                    G.add_node_attrs(node_id, {"full_function_call": full_name})
    return

def add_labels(G:NXGraph):
    nodes = G.nodes()
    for node_id in nodes:
        node = G.get_node(node_id)
        node_text = node["text"]
        G.add_node_attrs(node_id, {"label": node_text})
    return

def apply_post_transformations(G, aliases_dict):
    adjust_subscript(G)
    adjust_slice(G)
    #adjust_attributes_2(G)
    cleanup(G)
    connect_variables(G)
    add_library_attribute(G, aliases_dict)
    add_labels(G)
    return G


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
            subgraphs.append(get_ancestors_nodes(G, list(instance.values())[0]))
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


def transform_graph(G):
    # read json file
    f = open('knowledge_base/graph_clearing_patterns.json', "r")
    json_data = json.loads(f.read())

    flip_the_table(G)
    print_graph(G)

    aliases_dict = apply_pre_transformations(G)

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
            #print(f'line {counter} done in {end_iner - start_iner}')
    end_outer = time.time()
    # print(f'apply rule  done in {end_outer - start_outer}')

    apply_post_transformations(G, aliases_dict)
    print_graph(G)

    # create_subgraph(G, 1)

    # remove_descendants_from_node(G, 14)
    graph_dict = convert_graph_to_json(G)
    print(graph_dict)
    return graph_dict


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
