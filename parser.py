from rule_executioner import transform_graph
from tree_sitter import Language, Parser
import test_scripts
import time
from pyparsing import unicode
from regraph import NXGraph
import networkx as nx

def language_init():
    Language.build_library(
        # Store the library in the `build` directory
        'build/my-languages.so',

        # Include one or more languages
        [
            'parsers/tree-sitter-python',
            'parsers/tree-sitter-r',
            'parsers/tree-sitter-snakemake-pure'
        ]
    )


def parse(prog_language, code):
    """
    Parses given code into a tree
    :param prog_language: code language
    :param code: code to parse
    :return: tree-sitter
    """
    #if prog_language != "python" and prog_language != "r":
     #   print("Currently only Python and R are supported.")
      #  return

    language = Language('build/my-languages.so', prog_language)
    parser = Parser()
    parser.set_language(language)
    b = bytes(code, "utf8")
    tree = parser.parse(b)
    return tree


# traverses parsed nodes with Breadth-first search algorithm and
# returns the resulting networkx graph
def bfs_tree_traverser(tree):
    """
    Traverses a tree-sitter with Breadth-first search algorithm and converts it into an NXGraph
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
                G.add_node(node_id, attrs={"type": child_node.type, "text": child_node.text})
                # add edge between parent_node and child_node
                G.add_edge(parent_id, node_id)

                visited.append(child_node)
                queue.append(child_node)

        # set parent_id to the id of the next node in queue
        parent_id = parent_id + 1

    # access children example
    # id = 2
    # for child_id in G.successors(id):
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


def get_prop_type(value, key=None):
    """
    Performs typing and value conversion for the graph_tool PropertyMap class.
    If a key is provided, it also ensures the key is in a format that can be
    used with the PropertyMap. Returns a tuple, (type name, value, key)
    """
    if isinstance(key, unicode):
        # Encode the key as ASCII
        key = key.encode('ascii', errors='replace')

    # Deal with the value
    if isinstance(value, bool):
        tname = 'bool'

    elif isinstance(value, int):
        tname = 'float'
        value = float(value)

    elif isinstance(value, float):
        tname = 'float'

    elif isinstance(value, unicode):
        tname = 'string'
        value = value.encode('ascii', errors='replace')

    elif isinstance(value, dict):
        tname = 'object'

    else:
        tname = 'string'
        value = str(value)

    return tname, value, key


# call this function if you need to add languages to language.so library
language_init()


def main():

    language = 'python'
    code = test_scripts.Python.code_0
    start = time.time()
    tree_sitter = parse(language, code)

    # traverse tree-sitter -> get NXGraph
    nxgraph = bfs_tree_traverser(tree_sitter)
    G = transform_graph(nxgraph)

if __name__ == "__main__":
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
