import csv
from regraph import NXGraph, Rule, FiniteSet, plot_graph
import json
import ast
import time
import matplotlib.pyplot as plt
import networkx as nx
from regraph.backends.networkx.plotting import plot_rule


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


def apply_pre_transformations(G):
    """# redundant descendants
        redundant_descendants = [
            "keyword_argument"
        ]
        for redundancy in redundant_descendants:
            pattern = create_pattern("node_id", "type", redundancy)
            instances = G.find_matching(pattern)
            for instance in instances:
                remove_descendants_from_node(G, instance["node_id"])"""
    return G


def cleanup(G):
    # redundant parents
    redundancy_list = [
        "expression_statement",
        "assignment",
        "pattern_list",
        "call",
        "argument_list"
    ]
    for redundancy in redundancy_list:
        redundancy_pattern = create_pattern("node_id", "type", redundancy)
        instances = G.find_matching(redundancy_pattern)
        for instance in instances:
            remove_nodes(G, [instance["node_id"]])
    return


def compare_outputs_inputs(G, output_instances, input_instances, nodes_to_remove):
    # check if same names, remove both nodes, add edge
    for output_instance in output_instances:
        output_identifier = output_instance[2]
        #if output_identifier in removed_instances:
            #continue
        output_caller_function = output_instance[1]
        # print(output_caller_function)
        output_node = G.get_node(output_identifier)
        for input_instance in input_instances:
            input_identifier = input_instance[1]
            #if input_identifier in removed_instances:
                #continue
            input_caller_function = input_instance[2]
            # print(input_caller_function)
            input_node = G.get_node(input_identifier)
            # if same, remove nodes and add edge
            if output_node['text'] == input_node['text']:
                #G.remove_node(output_identifier)
                if output_identifier not in nodes_to_remove:
                    nodes_to_remove.append(output_identifier)
                #G.remove_node(input_identifier)
                if input_identifier not in nodes_to_remove:
                    nodes_to_remove.append(input_identifier)
                # add edge between caller functions
                # if exists, add further attribute
                try:
                    G.add_edge(output_caller_function, input_caller_function, {'text': output_node['text']})
                except:
                    G.add_edge_attrs(output_caller_function, input_caller_function, {'text': output_node['text']})

                continue

    return G, output_instances, input_instances, nodes_to_remove


def connect_variables(G):
    """
    1. search for childless identifiers
    2. search for parentless identifiers
    3. check if they have the same text values
    4. if yes, remove both, make edge between parent of 1 and child of 2
    5. save rest of identifiers as attribute of their parent or child respectfully
    """

    # if an identifier node is a child of a caller function, it is an output value of a function
    output_pattern = NXGraph()
    output_pattern.add_node(1, {'type': 'caller_function'})
    output_pattern.add_node(2, {'type': 'output'})
    output_pattern.add_edge(1, 2)

    # if an identifier node is a parent to any node, it is an input value into that function
    # check in known inputs
    input_pattern = NXGraph()
    input_pattern.add_node(1, {'type': 'input'})
    input_pattern.add_node(2)
    input_pattern.add_edge(1, 2)

    nodes_to_remove = []

    output_instances = G.find_matching(output_pattern)
    input_instances = G.find_matching(input_pattern)

    G, output_instances, input_instances, nodes_to_remove = compare_outputs_inputs(G, output_instances,
                                                                                     input_instances, nodes_to_remove)
    # go though leftover inputs, save them into their
    # belonging functions as attribute
    for input_instance in input_instances:

        input_id = input_instance[1]
        #if input_id in nodes_to_remove:
            #continue
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
        #G.remove_node(input_id)
        if input_id not in nodes_to_remove:
            nodes_to_remove.append(input_id)

    # check the rest of the potential inputs
    input_pattern = NXGraph()
    input_pattern.add_node(1, {'type': 'identifier'})
    input_pattern.add_node(2)
    input_pattern.add_edge(1, 2)

    input_instances = G.find_matching(input_pattern)
    G, output_instances, input_instances, nodes_to_remove = compare_outputs_inputs(G, output_instances,
                                                                                        input_instances, nodes_to_remove)
    for input_instance in input_instances:

        input_id = input_instance[1]
        #if input_id in nodes_to_remove:
            #continue
        children = G.successors(input_id)
        input_node = G.successors(input_id)
        # save attr in child
        input_node = G.get_node(input_id)
        child_id = list(children)[0]
        child_node = G.get_node(child_id)
        if "identifier" in child_node:
            for elem in input_node["text"]:
                child_node["identifier"].add(elem)
        else:
            child_node["identifier"] = input_node["text"]
        G.update_node_attrs(child_id, child_node)
        #G.remove_node(input_id)
        if input_id not in nodes_to_remove:
            nodes_to_remove.append(input_id)

    # go through leftover outputs, save them into their
    # belonging functions as attribute
    for output_instance in output_instances:

        output_id = output_instance[2]
        #if output_id in nodes_to_remove:
            #continue
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
        #G.remove_node(output_id)
        if input_id not in nodes_to_remove:
            nodes_to_remove.append(input_id)
    for id in nodes_to_remove:
        G.remove_node(id)
    return


def apply_post_transformations(G):
    cleanup(G)
    connect_variables(G)
    return


def arrange_variables():
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


def get_subgraphs(G, pattern, pattern_digraph):
    # find root
    root_id = [n for n, d in pattern_digraph.in_degree() if d == 0]
    root_node = pattern.get_node(root_id[0])

    # find all instances of root in graph
    root_pattern = NXGraph()
    root_pattern.add_node(root_id[0], root_node)
    instances = G.find_matching(root_pattern)
    subgraphs = []
    if instances:
        for instance in instances:
            subgraphs.append(create_subgraph(G, instance[1]))
    return subgraphs


def apply_rule(G, json_rule):
    rule = Rule.from_json(json_rule)
    pattern = rule.lhs

    # check if pattern is a tree
    nodes = pattern.nodes()
    edges = pattern.edges()
    pattern_digraph = nx.DiGraph()
    pattern_digraph.add_nodes_from(nodes)
    pattern_digraph.add_edges_from(edges)

    instances = []
    # get subgraphs
    if nx.is_tree(pattern_digraph):
        subgraphs = get_subgraphs(G, pattern, pattern_digraph)
        for subgraph in subgraphs:
            instances.extend(subgraph.find_matching(pattern))
    else:
        instances = G.find_matching(pattern)

    # instances = G.find_matching(pattern)
    if instances:
        print(json_rule)
        for instance in instances:
            G.rewrite(rule, instance)


def transform_graph(G):
    # read json file
    f = open('knowledge_base/graph_clearing_patterns.json', "r")
    json_data = json.loads(f.read())
    print_graph(G)
    apply_pre_transformations(G)

    start_outer = time.time()
    counter = 1
    with open("knowledge_base/rule_base.txt") as file:
        for line in file:
            start_iner = time.time()
            json_rule = read_rule_from_line(line)
            # if counter == 22:
            # print_graph(G)
            apply_rule(G, json_rule)
            # if counter == 21:
            # print_graph(G)
            end_iner = time.time()
            # print(f'line {counter} done in {end_iner - start_iner}')
            counter = counter + 1
    end_outer = time.time()
    print(f'apply rule  done in {end_outer - start_outer}')

    apply_post_transformations(G)
    print_graph(G)

    # create_subgraph(G, 1)

    # remove_descendants_from_node(G, 14)

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
