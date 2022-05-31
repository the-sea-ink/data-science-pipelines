from tree_sitter import Language, Parser
import networkx as nx
from regraph import NXGraph, Rule, plot_rule


def parse(prog_language, code):
    """
    Parses given code into a tree
    :param prog_language: code language
    :param code: code to parse
    :return: tree-sitter
    """
    if prog_language != "python" and prog_language != "r":
        print("Currently only Python and R are supported.")
        return

    language = Language('./build/my-languages.so', prog_language)
    parser = Parser()
    parser.set_language(language)
    tree = parser.parse(bytes(code, "utf8"))
    return tree


# traverses parsed nodes with Breadth-first search algorithm and
# returns the resulting networkx graph
def bfs_tree_traverser(tree):
    """
    Traverses a tree-sitter and converts it into an NXGraph
    :param tree: tree-sitter to be traversed
    :return: NXGraph after traversal of a tree-sitter tree
    """
    root_node = tree.root_node
    G = NXGraph()
    # node_id = id of current node being traversed
    # parent_id = id of the parent of the current node
    node_id, parent_id = 0, 0
    # lists to queue the nodes in order and identify already visited nodes
    visited, queue = [], []

    visited.append(root_node)
    queue.append(root_node)

    # add root_node to the graph
    G.add_node(0, attrs={"type": root_node.type, "text": root_node.text})

    # loop to visit each node
    while queue:
        node = queue.pop(0)

        for child_node in node.children:
            if child_node not in visited:
                node_id += 1
                # add child node to graph
                G.add_node(node_id, attrs={"type": child_node.type, "text": child_node.text, "parent_id":parent_id})
                # add edge between parent_node and child_node
                G.add_edge(parent_id, node_id)

                visited.append(child_node)
                queue.append(child_node)

        # set parent_id to the id of the next node in queue
        parent_id = parent_id + 1

    # access children example
    #root_id = 2
    #for child_id in G.successors(root_id):
    #    print(child_id, G.get_node(child_id))

    return G

def convert_nxgraph_to_graph(NXGraph):
    """
    Extracts and nx.Graph from the NXGraph
    :param NXGraph
    :return: nx.Graph
    """
    nxGraph = nx.Graph(NXGraph._graph)
    return nxGraph

# read code
code = b''
with open("bernoulli.py", "rb") as file:
    code += file.read()  # async read chunk
    code = code.decode('utf-8')

# parse code -> get tree-sitter
tree_sitter = parse('python', code)

# traverse tree-sitter -> get NXGraph
nxgraph = bfs_tree_traverser(tree_sitter)

# convert NXGraph -> get nx.Graph
graph = convert_nxgraph_to_graph(nxgraph)


