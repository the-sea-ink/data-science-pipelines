import ast
from tree_sitter import Language, Parser

from parser import ASTVisitor, graph


def py_init():
    Language.build_library(
        # Store the library in the `build` directory
        'build/my-languages.so',

        # Include one or more languages
        [
            'tree-sitter-python'
        ]
    )


def r_init():
    Language.build_library(
        # Store the library in the `build` directory
        'build/my-languages.so',

        # Include one or more languages
        [
            'tree-sitter-r'
        ]
    )


def parse_py(code):
    # TODO language check
    # language init
    # call this if you still need to add the language to the build directory:
    # py_init()

    PY_LANGUAGE = Language('./build/my-languages.so', 'python')
    python_parser = Parser()
    python_parser.set_language(PY_LANGUAGE)

    # get a tree
    tree = python_parser.parse(bytes(code, "utf8"))

    # traverse tree to get nodes & edges
    nodes, edges = [], []
    node = tree.root_node
    nodes, edges = tree_traverser(node)
    print(nodes)
    return


def parse_r(code):
    # language init
    # call this if you still need to add the language to the build directory:
    # r_init()

    R_LANGUAGE = Language('./build/my-languages.so', 'r')
    r_parser = Parser()
    r_parser.set_language(R_LANGUAGE)
    tree = r_parser.parse(bytes(code, "utf8"))
    print(tree.root_node.sexp())
    return


def parse_sm(code):
    return


def parse_ast(code):
    tree = ast.parse(code)

    inspector = ASTVisitor()
    inspector.visit(tree)

    for k, v in inspector.assigns.items():
        print(k, v)

    nodes, edges = graph(inspector)
    return nodes, edges


def tree_traverser(node):
    if node.child_count == 0:
        return [node], []

    result_nodes = list()
    result_edges = list()

    # recursive tree traversal
    for child_node in node.children:
        child_nodes, child_edges = tree_traverser(child_node)
        result_nodes = result_nodes + child_nodes
        result_edges = result_edges + child_edges
        result_edges.append((node, child_node))

    result_nodes.append(node)
    return result_nodes, result_edges


code = b''
with open("bernoulli.py", "rb") as file:
    code += file.read()  # async read chunk

# print(code.decode('utf-8'))
parse_py(code.decode('utf-8'))
