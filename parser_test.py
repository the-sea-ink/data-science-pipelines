import ast
from tree_sitter import Language, Parser

from parser import ASTVisitor, graph


def parse_py(code):
    # TODO language check
    # TODO fit the ASTVisitor class to tree-sitter structure
    PY_LANGUAGE = Language('./build/my-languages.so', 'python')
    python_parser = Parser()
    python_parser.set_language(PY_LANGUAGE)
    tree = python_parser.parse(bytes(code, "utf8"))
    print(tree.root_node.sexp())
    return


def parse_r(code):
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


code = b''
with open("sklearn_example.py", "rb") as file:
    code += file.read()  # async read chunk

# print(code.decode('utf-8'))
parse_py(code.decode('utf-8'))
