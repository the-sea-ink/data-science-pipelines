from builder_functions.graph_builder import bfs_tree_traverser
from builder_functions.pattern_builder import rewrite_graph, clear_graph, rename_graph_types, \
    convert_graph_to_json, arrange_graph
from tree_sitter import Language, Parser
import test_scripts
from regraph import NXGraph, Rule
from regraph.backends.networkx.plotting import plot_rule


def language_init():
    Language.build_library(
        # Store the library in the `build` directory
        'build/my-languages.so',

        # Include one or more languages
        [
            'playground/parsers/tree-sitter-python',
            'playground/parsers/tree-sitter-r',
            'playground/parsers/tree-sitter-snakemake-pure'
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
    tree = parser.parse(bytes(code, "utf8"))
    return tree

# call this function if you need to add languages to language.so library
language_init()

language = 'r'
code = test_scripts.R.code_2

#language = 'python'
#code = test_scripts.Python.code_5

#language = 'snakemake'
#code = test_scripts.Snakemake.code_1

# parse code with tree-sitter
tree_sitter = parse(language, code)
print(tree_sitter)
# traverse tree-sitter -> get NXGraph
nxgraph = bfs_tree_traverser(tree_sitter)

# rewrite graph
rename_graph_types(nxgraph, language)
G = clear_graph(nxgraph)
G = arrange_graph(G)
G = rewrite_graph(G, language)
json_graph = convert_graph_to_json(G)


