import networkx as nx
from regraph import NXGraph
from utils import print_graph, nxraph_to_digraph, draw_diffgraph, draw_graph


def calculate_diff_graph(G1: NXGraph, G2: NXGraph):
    # add G1 nodes to Gdiff, label them as of G1 origin, add nodes to hash table
    Gdiff = NXGraph()
    hash_table_nodes, nodes_to_add, nodes_to_delete, nodes_to_update = {}, {}, {}, {}
    hash_table_edges, edges_to_add, edges_to_delete = [], [], []
    for g1_node, g1_attr in G1.nodes(data=True):
        hash_table_nodes[g1_node] = g1_attr.copy()
        g1_attr["origin"] = "G1"
        Gdiff.add_node(g1_node, g1_attr)
        nodes_to_delete[g1_node] = g1_attr

    # traverse G2 and check if a node is in the Gdiff graph yet
    for g2_node, g2_attr in G2.nodes(data=True):
        # same node present in both graphs
        if g2_node in hash_table_nodes and hash_table_nodes[g2_node] == g2_attr:
            Gdiff.add_node_attrs(g2_node, {"origin": "G2"})
            nodes_to_delete.pop(g2_node)
        # same node, new attrs
        elif g2_node in hash_table_nodes:
            hash_table_nodes[g2_node] = g2_attr.copy()
            nodes_to_update[g2_node] = {}
            nodes_to_update[g2_node]["old"] = G1.get_node(g2_node)
            nodes_to_update[g2_node]["new"] = g2_attr.copy()
            g2_attr["origin"] = "updated"
            Gdiff.update_node_attrs(g2_node, g2_attr)
            nodes_to_delete.pop(g2_node)
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
    # print_graph(Gdiff)
    return Gdiff, nodes_to_add, nodes_to_update, nodes_to_delete, edges_to_add, edges_to_delete


# TODO add case if there is no path between nodes
def find_subgraph_from_node_list(G: nx.DiGraph, changed_nodes: list, new_nodes: list):
    # remove G2 only edges from G
    edges_to_remove = {}
    for s, t, attrs in G.edges(data=True):
        if len(attrs["origin"]) == 1:
            for elem in attrs["origin"]:
                if elem == "G2":
                    edges_to_remove[(s, t)] = attrs
    for edge in edges_to_remove:
        G.remove_edge(edge[0], edge[1])

    # create all combinations
    H = nx.to_undirected(G)
    print(changed_nodes)
    paths = []
    for i in range(len(changed_nodes) - 1):
        if len(changed_nodes) == 1:
            paths.append(i)
        paths.append((changed_nodes[0], changed_nodes[i + 1]))

    # create paths between node combinations
    subgraph_nodes = nx.Graph()
    nodes_in_subgraph = []
    longest_induced_path = []
    for path in paths:
        if path[0] in nodes_in_subgraph and path[1] in nodes_in_subgraph:
            continue
        longest_induced_path.extend(nx.shortest_path(H, *path))
        nodes_in_subgraph.extend(longest_induced_path)

    # find nodes that are not to be deleted
    nodes_to_stay = list(set(nodes_in_subgraph) - set(changed_nodes))

    # bring back the deleted edges
    for edge in edges_to_remove:
        G.add_edge(edge[0], edge[1], origin="G2")

    # find path to newly added nodes
    if new_nodes:
        for node in new_nodes:
            longest_induced_path.extend(nx.shortest_path(H, node, nodes_to_stay[0]))
            nodes_in_subgraph.extend(longest_induced_path)

    subgraph_nodes.add_nodes_from(longest_induced_path)
    # create subgraph
    subgraph = nx.subgraph(G, subgraph_nodes)
    #print_graph(subgraph)

    # trim G2 nodes and edges
    nodes_to_remove = []
    edges_to_remove = []
    for s, t, attrs in subgraph.edges(data=True):
        if len(attrs["origin"]) == 1:
            for elem in attrs["origin"]:
                if elem == "G2":
                    edges_to_remove.append((s, t))

    for id, attrs in subgraph.nodes(data=True):
        if len(attrs["origin"]) == 1:
            for elem in attrs["origin"]:
                if elem == "G2":
                    nodes_to_remove.append(id)

    pattern = nx.DiGraph(subgraph)
    # print_graph(pattern)
    pattern.remove_edges_from(edges_to_remove)
    # print_graph(pattern)
    pattern.remove_nodes_from(nodes_to_remove)
    # print_graph(pattern)
    return pattern


def translate_changes_into_rule(Gdiff, pattern, nodes_to_add, nodes_to_update, nodes_to_delete, edges_to_add,
                                edges_to_delete):
    # adjust pattern remove extra attributes

    # add nodes

    # update nodes

    # delete nodes

    # add edges

    # delete edges
    print("pattern:")
    print_graph(pattern)
    return


def test_diff():
    G1, G2 = NXGraph(), NXGraph()
    G1.add_nodes_from([(0, {"type": "function", "text": "A"}),
                       (1, {"text": "B"}),
                       (2, {"text": "D"}),
                       (3, {"text": "E"}),
                       (4, {"text": "F"})])
    G1.add_edges_from([(1, 0), (0, 2), (0, 3), (3, 4)])

    G2.add_nodes_from([(0, {"type": "function", "text": "A"}),
                       (1, {"text": "C"}),
                       (2, {"text": "D"}),
                       (3, {"text": "E"})])
    G2.add_edges_from([(1, 0), (0, 2), (2, 3)])

    Gdiff, nodes_to_add, nodes_to_update, nodes_to_delete, edges_to_add, edges_to_delete = calculate_diff_graph(G1, G2)

    changed_nodes, new_nodes = [], []
    changed_nodes.extend(list(nodes_to_delete.keys()))
    changed_nodes.extend(list(nodes_to_update.keys()))
    new_nodes.extend(list(nodes_to_add.keys()))

    # add all nodes involved in edge changes
    for edge in edges_to_delete:
        if edge[0] not in changed_nodes:
            changed_nodes.append(edge[0])
        if edge[1] not in changed_nodes:
            changed_nodes.append(edge[1])

    for edge in edges_to_add:
        if edge[0] not in changed_nodes and edge[0] not in new_nodes:
            changed_nodes.append(edge[0])
        if edge[1] not in changed_nodes and edge[1] not in new_nodes:
            changed_nodes.append(edge[1])

    # transform NXGraph into an nx DiGraph
    GDidiff = nxraph_to_digraph(Gdiff)
    G1 = nxraph_to_digraph(G1)
    G2 = nxraph_to_digraph(G2)

    draw_graph(G1)
    draw_graph(G2)
    draw_diffgraph(GDidiff)

    pattern = find_subgraph_from_node_list(GDidiff, changed_nodes, new_nodes)
    translate_changes_into_rule(GDidiff, pattern, nodes_to_add, nodes_to_update, nodes_to_delete, edges_to_add,
                                edges_to_delete)


def test_subgraph():
    G = nx.DiGraph()
    edges = [(7, 4), (3, 8), (3, 2), (3, 0), (3, 1), (7, 5), (7, 6), (7, 8), (8, 9)]
    G.add_edges_from(edges)
    nodelist = [0, 4, 6, 7, 9]
    subgraph = find_subgraph_from_node_list(G, nodelist)


# test_subgraph()
test_diff()
