import networkx as nx
from regraph import NXGraph
from utils import print_graph


# TODO add saving changed nodes
def calculate_diff_graph(G1: NXGraph, G2: NXGraph):
    # add G1 nodes to Gdiff, label them as of G1 origin, add nodes to hash table
    Gdiff = NXGraph()
    hash_table = {}
    for g1_node, g1_attr in G1.nodes(data=True):
        hash_table[g1_node] = g1_attr.copy()
        g1_attr["origin"] = "G1"
        Gdiff.add_node(g1_node, g1_attr)

    # traverse G2 and check if a node is in the Gdiff graph yet
    for g2_node, g2_attr in G2.nodes(data=True):
        # same node, nothing changed
        if g2_node in hash_table and hash_table[g2_node] == g2_attr:
            Gdiff.add_node_attrs(g2_node, {"origin": "G2"})
        # same node, new attrs
        elif g2_node in hash_table:
            hash_table[g2_node] = g2_attr.copy()
            g2_attr["origin"] = "G2"
            Gdiff.update_node_attrs(g2_node, g2_attr)
        # new node
        else:
            hash_table[g2_node] = g2_attr.copy()
            g2_attr["origin"] = "G2"
            Gdiff.add_node(g2_node, g2_attr)
    print_graph(Gdiff)

    # add all E1 edges to diff graph and to hash table, label them as of G1 origin
    for s, t in G1.edges():
        print("\t{}->{}".format(s, t))
    return Gdiff


# TODO add case if there is no path between nodes
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


def test_subgraph():
    G = nx.DiGraph()
    edges = [(7, 4), (3, 8), (3, 2), (3, 0), (3, 1), (7, 5), (7, 6), (7, 8), (8, 9)]
    G.add_edges_from(edges)
    nodelist = [0, 4, 6, 7, 9]
    subgraph = find_subgraph_from_node_list(G, nodelist)
    print_graph(subgraph)


# test_subgraph()

def test_diff():
    G1, G2 = NXGraph(), NXGraph()
    G1.add_nodes_from([(0, {"type": "root"}), (1, {"type": "child"}), (2, {"type": "child"}), (3, {"type": "child"}),
                       (4, {"type": "child"}), (6, {"type": "child"})])
    G1.add_edges_from([(0, 1), (1, 2), (0, 3), (2, 4), (4, 6)])

    G2.add_nodes_from([(0, {"type": "root"}), (1, {"type": "leaf"}), (2, {"type": "child"}), (3, {"type": "child"}),
                       (4, {"type": "child"}), (5, {"type": "child"})])
    G2.add_edges_from([(0, 1), (1, 2), (0, 3), (2, 4), (4, 5)])

    calculate_diff_graph(G1, G2)


test_diff()
