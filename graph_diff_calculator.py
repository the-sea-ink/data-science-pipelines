import networkx as nx
from regraph import NXGraph
from utils import print_graph, nxraph_to_digraph
from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib.pyplot as plt


def calculate_diff_graph(G1: NXGraph, G2: NXGraph):
    # add G1 nodes to Gdiff, label them as of G1 origin, add nodes to hash table
    Gdiff = NXGraph()
    hash_table_nodes, nodes_to_add, nodes_to_update = {}, {}, {}
    hash_table_edges, nodes_to_delete, edges_to_add, edges_to_delete = [], [], [], []
    for g1_node, g1_attr in G1.nodes(data=True):
        hash_table_nodes[g1_node] = g1_attr.copy()
        g1_attr["origin"] = "G1"
        Gdiff.add_node(g1_node, g1_attr)
        nodes_to_delete.append(g1_node)

    # traverse G2 and check if a node is in the Gdiff graph yet
    for g2_node, g2_attr in G2.nodes(data=True):
        # same node present in both graphs
        if g2_node in hash_table_nodes and hash_table_nodes[g2_node] == g2_attr:
            Gdiff.add_node_attrs(g2_node, {"origin": "G2"})
            nodes_to_delete.remove(g2_node)
        # same node, new attrs
        elif g2_node in hash_table_nodes:
            hash_table_nodes[g2_node] = g2_attr.copy()
            nodes_to_update[g2_node] = g2_attr.copy()
            g2_attr["origin"] = "updated"
            Gdiff.update_node_attrs(g2_node, g2_attr)
            nodes_to_delete.remove(g2_node)
        # new node
        else:
            hash_table_nodes[g2_node] = g2_attr.copy()
            nodes_to_add[g2_node] = g2_attr.copy()
            g2_attr["origin"] = "G2"
            Gdiff.add_node(g2_node, g2_attr)

    # add all E1 edges to diff graph and to hash table, label them as of G1 origin
    for s, t in G1.edges():
        hash_table_edges.append((s, t))
        edge_attr = {"origin": "G1"}
        Gdiff.add_edge(s, t, edge_attr)
        edges_to_delete.append((s, t))

    # traverse E2 and check if current edge is in the Gdiff graph yet
    for s, t in G2.edges():
        # same edge present in both graphs
        if (s, t) in hash_table_edges:
            Gdiff.add_edge_attrs(s, t, {"origin": "G2"})
            edges_to_delete.remove((s, t))
        # new edge
        else:
            Gdiff.add_edge(s, t, {"origin": "G2"})
            edges_to_add.append((s, t))
    print_graph(Gdiff)
    return Gdiff, nodes_to_add, nodes_to_update, nodes_to_delete, edges_to_add, edges_to_delete


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


def translate_changes_into_rule(Gdiff, pattern, nodes_to_add, nodes_to_update, nodes_to_delete, edges_to_add,
                                edges_to_delete):
    return


def test_diff():
    G1, G2 = NXGraph(), NXGraph()
    G1.add_nodes_from([(0, {"type": "A"}), (1, {"type": "B"}), (2, {"type": "D"}), (3, {"type": "E"}),
                       (4, {"type": "F"}), (6, {"type": "H"})])
    G1.add_edges_from([(0, 1), (1, 2), (0, 3), (2, 4), (4, 6)])

    G2.add_nodes_from([(0, {"type": "A"}), (1, {"type": "C"}), (2, {"type": "D"}), (3, {"type": "E"}),
                       (4, {"type": "F"}), (5, {"type": "G"})])
    G2.add_edges_from([(0, 1), (1, 2), (0, 3), (3, 4), (4, 5)])

    Gdiff, nodes_to_add, nodes_to_update, nodes_to_delete, edges_to_add, edges_to_delete = calculate_diff_graph(G1, G2)
    changed_nodes = []
    changed_nodes.extend(nodes_to_delete)
    changed_nodes.extend(list(nodes_to_add.keys()))
    changed_nodes.extend(list(nodes_to_update.keys()))
    for edge in edges_to_delete:
        if edge[0] not in changed_nodes:
            changed_nodes.append(edge[0])
        elif edge[1] not in changed_nodes:
            changed_nodes.append(edge[1])
    print(changed_nodes)

    # transform NXGraph into an nx DiGraph
    GDidiff = nxraph_to_digraph(Gdiff)
    print_graph(GDidiff)

    # construct graph
    labels = nx.get_node_attributes(GDidiff, 'type')
    pos = graphviz_layout(GDidiff, prog="dot")
    # color different nodes depending on the labels
    val_map = {"both": "orange",
               "G1": "red",
               "G2": "green",
               "updated": "lightblue"
               }
    node_colors = []
    for node, attrs in GDidiff.nodes(data=True):
        if len(attrs["origin"]) == 2:
            node_colors.append(val_map["both"])
        elif len(attrs["origin"]) == 1:
            for elem in attrs["origin"]:
                if elem == "G1":
                    node_colors.append(val_map["G1"])
                elif elem == "G2":
                    node_colors.append(val_map["G2"])
                elif elem == "updated":
                    node_colors.append(val_map["updated"])
    edge_colors = []
    for s, t, attrs in GDidiff.edges(data=True):
        if len(attrs["origin"]) == 2:
            edge_colors.append(val_map["both"])
        elif len(attrs["origin"]) == 1:
            for elem in attrs["origin"]:
                if elem == "G1":
                    edge_colors.append(val_map["G1"])
                elif elem == "G2":
                    edge_colors.append(val_map["G2"])
    # add labels=labels, for different labeling
    # add node_color='lightblue' for one colored nodes
    nx.draw(GDidiff, pos=pos,
            with_labels=True,
            cmap=plt.get_cmap('inferno'),
            node_color=node_colors,
            edge_color=edge_colors,
            labels=labels,
            alpha=0.9,
            width=4,
            node_size=2200,
            arrowsize=20)
    plt.show()


def test_subgraph():
    G = nx.DiGraph()
    edges = [(7, 4), (3, 8), (3, 2), (3, 0), (3, 1), (7, 5), (7, 6), (7, 8), (8, 9)]
    G.add_edges_from(edges)
    nodelist = [0, 4, 6, 7, 9]
    subgraph = find_subgraph_from_node_list(G, nodelist)


# test_subgraph()
test_diff()
