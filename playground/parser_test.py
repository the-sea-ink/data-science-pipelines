import ast
from tree_sitter import Language, Parser

from parser import ASTVisitor, graph



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