import collections
import csv
import pandas as pd
from regraph import NXGraph, Rule
import json


def remove_descendants(G, node_type, instances, rule):
    #print(node_type)
    removed_nodes = []
    for ins in instances:
        node_id = ins[node_type]
        #print(str(node_id) + ":")
        # handling nested function calls;
        # checking if we deleted a subgraph of a nested function yet
        if node_id not in removed_nodes:
            desc = G.descendants(node_id)
            #print(desc)
            for id in list(desc):
                G.remove_node(id)
                removed_nodes.append(id)
    return removed_nodes


def remove_nodes(G, ids):
    for id in ids:
        G.remove_node(id)
    return


# removes all the nodes and edges of all nodes in rule whose ids
# are not in the list
def remove_everything_else(ids, rule, num_nodes):
    for i in range(num_nodes):
        if i not in ids:
            rule.inject_remove_node(i)
    return rule


# gets the ids of all of the nodes of a certain "type" in an instance of a graph
def get_ids(node_type, instances):
    ids = []
    for ins in instances:
        node_id = ins[node_type]
        ids.append(node_id)
    return ids


# creates a pattern to filter a graph based on "node type"
# attr_name -> name given to the variable used to identify this node type
# node_type -> the type of node that wants to be filtered
def create_simple_pattern(attr_name, node_type):
    pattern = NXGraph()
    pattern.add_node(attr_name)
    pattern.add_node_attrs(attr_name, {"type": node_type})
    return pattern


# creates a subgraph of the nodes given in ids, searches for their descendants that match the different given patterns
# and adds the text attribute of nodes that match those patterns as an attribute to the ascendant node
def add_attrs_from_patterns(ids, patterns, is_import, G):
    """

    :param ids: parent IDs with important descendant nodes
    :param patterns: patterns of descendant nodes
    :param is_import:
    :param G: graph
    :return:
    """
    for id in ids:
        subg_nodes = list(G.descendants(id)) if is_import else list(G.successors(id))
        subg_nodes.append(id)
        subgraph = G.generate_subgraph(G, subg_nodes)
        #print_graph(subgraph)
        for pattern in patterns:
            instances = subgraph.find_matching(pattern)
            if len(instances) > 0:
                sub_id = get_ids(list(pattern._graph.nodes._nodes)[0], instances)
                #print(sub_id)
                for i in range(len(sub_id)):
                    node_attributes = {list(pattern._graph.nodes._nodes)[0]: subgraph.get_node(sub_id[i])["text"]}
                    #print(node_attributes)
                    G.add_node_attrs(id, attrs=node_attributes)

def create_subgraph(G, node_id):
    subg_nodes = list(G.descendants(node_id))
    subgraph = G.generate_subgraph(G, subg_nodes)
    #print_graph(subgraph)
    rule = Rule.from_transform(subgraph)
    #plot_rule(rule)
    return subgraph

# adds an edge between the parent of a node and all the children of that same node (grandparent - grandchildren
# connection) this is necessary in order to later be able to remove those nodes that only serve as connectors
def connect_parent_and_children(G, ids, rule):
    for id in ids:
        parent_id = list(G.predecessors(id))[0]
        for child_id in list(G.successors(id)):
            rule.inject_add_edge(parent_id, child_id)
    return rule


def print_graph(G):
    print("List of nodes: ")
    for n, attrs in G.nodes(data=True):
        print("\t", n, attrs)
    """
    print("List of edges: ")
    for s, t, attrs in G.edges(data=True):
        print("\t{}->{}".format(s, t), attrs)
    """


def clear_graph(G):
    # create rule
    rule = Rule.from_transform(G)

    # print graph
    # print_graph(G)
    # subgraph = create_subgraph(G, 5)
    # print_graph(subgraph)

    # read json file
    f = open('graph_clearing_patterns.json', "r")
    json_data = json.loads(f.read())

    # handle redundancies
    redundand_patterns = []
    for key in json_data["redundancies"]:
        value = json_data["redundancies"][key]
        pattern = create_simple_pattern(key, value)
        redundand_patterns.append(pattern)
    i = 0
    redundand_ids = []
    for pattern in redundand_patterns:
        instances = G.find_matching(pattern)
        if len(instances) != 0:
            pattern_name = list(redundand_patterns[i]._graph.nodes._nodes)[0]
            redundand_id = get_ids(pattern_name, instances)
            redundand_ids += redundand_id
        i += 1
    remove_nodes(G, redundand_ids)

    # handle nodes with descendants that contain necessary attributes
    for node in json_data["nodes_with_descendants"]:
        # find parent node
        parent_pattern = create_simple_pattern(node, node)
        instances = G.find_matching(parent_pattern)

        # get ids of all parent occurrences in the graph
        if len(instances) != 0:
            parent_type = list(parent_pattern._graph.nodes._nodes)[0]
            #print(parent_type)
            parent_ids = get_ids(parent_type, instances)

            # find its children names in json
            descendants_patterns = []
            for descendant_node in json_data["nodes_with_descendants"][node]:
                descendant_pattern = create_simple_pattern(descendant_node, descendant_node)
                descendants_patterns.append(descendant_pattern)

            # get attributes of children
            if parent_type == "import_statement" or parent_type == "import_from_statement" or parent_type == "expression_statement":
                add_attrs_from_patterns(parent_ids, descendants_patterns, True, G)
            else:
                add_attrs_from_patterns(parent_ids, descendants_patterns, False, G)
            # clear descendants
            remove_descendants(G, parent_type, instances, rule)

    # handle simple nodes
    for node in json_data["simple_nodes"]:
        pattern = create_simple_pattern(json_data["simple_nodes"][node], json_data["simple_nodes"][node])
        instances = G.find_matching(pattern)
        if len(instances) != 0:
            pattern_type = list(pattern._graph.nodes._nodes)[0]
            remove_descendants(G, pattern_type, instances, rule)

    # handle comments
    for node in json_data["nodes_to_completely_remove"]:
        patterns_to_remove = create_simple_pattern(node, node)
        instances = G.find_matching(patterns_to_remove)
        if len(instances) != 0:
            node_type = list(patterns_to_remove._graph.nodes._nodes)[0]
            node_ids = get_ids(node_type, instances)
            remove_nodes(G, node_ids)

    print_graph(G)
    return G


def rewrite_graph(G):
    # read data from knowledge base
    df = pd.read_csv("signatures.csv")
    mapping = dict(zip(df.name, df.category))

    # read json file
    f = open('rewrite_rules.json', "r")
    json_data = json.loads(f.read())

    # replace function calls
    for node in json_data:
        # get one node type from the rewrite rules file (loop 1)
        pattern = create_simple_pattern(node, node)
        instances = G.find_matching(pattern)
        # For this specific node, find attribute type to read
        # acc. to rewrite rules (loop 2 if there is more than one)
        attr_type = list(json_data[node].keys())[0]
        # print(attr_type)
        # for this node type, find all graph nodes
        if len(instances) != 0:
            pattern_type = list(pattern._graph.nodes._nodes)[0]
            pattern_ids = get_ids(pattern_type, instances)
            # print(pattern_ids)
            # read attribute type for each node in pattern_ids
            for pattern_id in pattern_ids:
                node_attributes = G.get_node(pattern_id).get(attr_type)
                # print(node_attributes)
                # compare each attribute text with signatures (loop 3)
                if len(node_attributes) != 0:
                    for attribute_bytes in node_attributes:
                        attribute = attribute_bytes.decode("utf-8")
                        for name in mapping:
                            if attribute == name:
                                new_attribute = {'type': mapping[name]}
                                G.update_node_attrs(pattern_id, new_attribute)
    print_graph(G)
    return G