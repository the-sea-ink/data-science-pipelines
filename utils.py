from regraph.backends.networkx.graphs import NXGraph
import networkx as nx


def get_root_node_id(G: NXGraph):
    # TODO: rewrite to search for a real root node
    root_node = 0
    return root_node


def create_graph_from_pattern(pattern):
    # check if pattern is a connected graph
    nodes = pattern.nodes()
    edges = pattern.edges()
    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
    return graph


def pattern_connected(pattern: NXGraph):
    return nx.is_connected(create_graph_from_pattern(pattern))


def remove_nodes(G, ids):
    for id in ids:
        G.remove_node(id)
    return


# creates a pattern to filter a graph based on "node type"
# attr_name -> name given to the variable used to identify this node type
# node_type -> the type of node that wants to be filtered
def create_pattern(id, attr_name, node_type):
    pattern = NXGraph()
    pattern.add_node(id, {attr_name: node_type})
    return pattern


# TODO restrict subgraph deepness
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


def print_nodes(graph, node_ids):
    for id in node_ids:
        print(graph.get_node(id))

