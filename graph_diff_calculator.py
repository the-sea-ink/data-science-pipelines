import networkx as nx
from regraph import NXGraph
from utils import print_graph

def find_subgraph_from_node_list(G: nx.DiGraph, nodelist: list):
    # create all combinations
    H = nx.to_undirected(G)
    paths = []
    for i in range(len(nodelist) - 1):
        if len(nodelist) == 1:
            paths.append(i)
        paths.append((nodelist[0], nodelist[i + 1]))

    # create paths between combinations
    subgraph_nodes = nx.Graph()
    nodes_in_subgraph = []
    for path in paths:
        if path[0] in nodes_in_subgraph or path[1] in nodes_in_subgraph:
            continue
        longest_induced_path = nx.shortest_path(H, *path)
        nodes_in_subgraph.append(longest_induced_path)
        subgraph_nodes.add_nodes_from(longest_induced_path)

    # create subgraph
    subgraph = nx.subgraph(G, subgraph_nodes)
    return subgraph


def test():
    G = nx.DiGraph()
    edges = [(7, 4), (3, 8), (3, 2), (3, 0), (3, 1), (7, 5), (7, 6), (7, 8), (8, 9)]
    G.add_edges_from(edges)
    nodelist = [0, 4, 6, 7, 9]
    subgraph = find_subgraph_from_node_list(G, nodelist)
    print_graph(subgraph)


test()