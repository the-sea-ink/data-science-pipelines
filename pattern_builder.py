from tree_sitter import Language, Parser
import networkx as nx
import matplotlib.pyplot as plt
from regraph import NXGraph, Rule
from regraph import plot_graph, plot_instance, plot_rule
import json

def remove_descendants(G, node_type, instances, rule):
    print(node_type)
    for ins in instances:
        node_id = ins[node_type]
        print(str(node_id) + ":")
        desc = G.descendants(node_id)
        print(desc)
        for id in list(desc):
            G.remove_node(id)
    return rule


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

def create_pattern_with_descendants(pattern_dict):
    pattern = NXGraph()

    return

# creates a subgraph of the nodes given in ids, searches for their descendants that match the different given patterns
# and adds the text attribute of nodes that match those patterns as an attribute to the ascendant node
def add_attrs_from_patterns(ids, patterns, is_import, G):
    for id in ids:
        subg_nodes = list(G.descendants(id)) if is_import else list(G.successors(id))
        subg_nodes.append(id)
        subgraph = G.generate_subgraph(G, subg_nodes)

        for pattern in patterns:
            instances = subgraph.find_matching(pattern)
            sub_id = get_ids(list(pattern._graph.nodes._nodes)[0], instances)
            node_attributes = {list(pattern._graph.nodes._nodes)[0] : subgraph.get_node(sub_id[0])["text"]}
            G.add_node_attrs(id, attrs=node_attributes)


# adds an edge between the parent of a node and all the children of that same node (grandparent - grandchildren connection)
# this is necessary in order to later be able to remove those nodes that only serve as connectors
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
    print("List of edges: ")
    for s, t, attrs in G.edges(data=True):
        print("\t{}->{}".format(s, t), attrs)


def create_patterns():
    # read json file with patterns
    f = open('patterns.json', "r")
    data = json.loads(f.read())

    # create and fill list of patterns
    patterns = []
    for key in data:
        value = data[key]
        pattern = create_simple_pattern(key, value)
        patterns.append(pattern)

    return patterns


"""
def match_patterns(G, rule, patterns):

    i = 0
    for pattern in patterns:
        instance = G.find_matching(pattern)
        # getting the name of the pattern
        pattern_name = list(patterns[i]._graph.nodes._nodes)[0]
        rule = remove_descendants(G, pattern_name, instance, rule)
        i += 1

    return rule
"""


def rewrite_graph(G):
    # create rule
    rule = Rule.from_transform(G)

    # print graph
    print_graph(G)

    # read json file
    f = open('patterns.json', "r")
    json_data = json.loads(f.read())

    # find redundancies
    redundand_patterns = []
    for key in json_data["redundancies"]:

        # find nodes with necessary attributes in the graph
        value = json_data["redundancies"][key]
        pattern = create_simple_pattern(key, value)
        redundand_patterns.append(pattern)

    # remove redundancies
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
    #plot_rule(rule)

    # find nodes with descendants
    parent_patterns = []
    for node in json_data["nodes_with_descendants"]:
        # find parent node
        parent_pattern = create_simple_pattern(node, node)
        instances = G.find_matching(parent_pattern)

        # get ids of all parent occurrences in the graph
        if len(instances) != 0:
            parent_type = list(parent_pattern._graph.nodes._nodes)[0]
            parent_ids = get_ids(parent_type, instances)

            # find its children names in json
            descendants_patterns = []
            for descendant_node in json_data["nodes_with_descendants"][node]:
                descendant_pattern = create_simple_pattern(descendant_node, descendant_node)
                descendants_patterns.append(descendant_pattern)

            # get attributes of children
            if parent_type == "import_statement":
                add_attrs_from_patterns(parent_ids, descendants_patterns, True, G)
            else:
                add_attrs_from_patterns(parent_ids, descendants_patterns, False, G)
            remove_descendants(G, parent_type, instances, rule)

    #G.rewrite(rule, rule.p)
    print_graph(G)
    return
