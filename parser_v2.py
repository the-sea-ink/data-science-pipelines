from builder_functions.graph_builder import bfs_tree_traverser
from builder_functions.pattern_builder import transform_graph, \
    convert_graph_to_json, print_graph
from tree_sitter import Language, Parser
import test_scripts
import time
from regraph import NXGraph, Rule
from regraph.backends.networkx.plotting import plot_rule


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

# call this function if you need to add languages to language.so library
language_init()


def main():

    language = 'python'
    code = test_scripts.Python.code_0
    start = time.time()
    tree_sitter = parse(language, code)

    # traverse tree-sitter -> get NXGraph
    nxgraph = bfs_tree_traverser(tree_sitter)
    #print_graph(nxgraph)

    # rewrite graph
    #rename_graph_types(nxgraph, language)


    G = transform_graph(nxgraph)


    #G = convert_graph_to_json(G)

if __name__ == "__main__":
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
