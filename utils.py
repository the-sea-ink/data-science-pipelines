from regraph.backends.networkx.graphs import NXGraph
import networkx as nx


def get_root_node_id(G: NXGraph):
    ##TODO: rewrite to search for a real root node
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
