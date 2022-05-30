from tree_sitter import Language, Parser
import networkx as nx
from regraph import NXGraph, Rule, plot_rule


def parse(prog_language, code):
    # if prog_language != "python" and prog_language != "r":
    #   print("Currently only Python and R are supported.")
    #  return

    language = Language('./build/my-languages.so', prog_language)
    parser = Parser()
    parser.set_language(language)
    tree = parser.parse(bytes(code, "utf8"))

    return bfs_tree_traverser(tree.root_node, NXGraph())


# traverses parsed nodes with Breadth-first search algorithm and
# returns the resulting networkx graph
def bfs_tree_traverser(root_node, G):
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

    return G


code = b''
with open("bernoulli.py", "rb") as file:
    code += file.read()  # async read chunk

parse('python', code.decode('utf-8'))
