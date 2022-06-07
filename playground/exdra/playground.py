from regraph import NXGraph, Rule, plot_rule, plot_graph
from tree_sitter import Language, Parser
import uuid
import json


JSON_LANGUAGE = Language('../parsers/build/my-languages.so', 'json')

def get_graph(tree, lang):
    root_node = tree.root_node
    G = NXGraph()
    parent_id, node_id = 0, 0
    visited, queue = [], []

    visited.append(root_node)
    queue.append(root_node)

    G.add_node(node_id, attrs={"type": root_node.type, "text": root_node.text})

    while queue:
        node = queue.pop(0)

        for child_node in node.children:
            if child_node not in visited:
                node_id += 1
                _dict = {
                    "type": child_node.type,
                    "text": child_node.text,
                    "parent_id": parent_id,
                    "language": lang
                }
                G.add_node(node_id, attrs=_dict)
                G.add_edge(parent_id, node_id)

                visited.append(child_node)
                queue.append(child_node)

        parent_id += 1

    return G


def walk(graph):
    def __walk(_id, level=0):
        node = graph.get_node(_id)
        print(f'{"  "*level} {node["text"]} ({_id}, {node["type"]})')
        for child_id in graph.successors(_id):
            __walk(child_id, level+1)

    # In case the root node with ID 0 was removed, start with the node
    # that has the smallest ID.
    __walk(min(graph.nodes()))


def finiteset2json(fset):
    return json.loads(fset.to_json()["data"][0])


def main():
    parser = Parser()
    parser.set_language(JSON_LANGUAGE)

    tree = parser.parse(bytes(open('examples/saved_pipeline.json').read(), "utf8"))
    graph = get_graph(tree, lang=JSON_LANGUAGE.name)

    for sign in ["\"", ",", "{", "}", ":", "[", "]", "string_content"]:
        pattern = NXGraph()
        pattern.add_node("x", {"type": sign})
        rule = Rule.from_transform(pattern)
        rule.inject_remove_node("x")

        for instance in graph.find_matching(pattern):
            graph.rewrite(rule, instance)

    pattern = NXGraph()
    pattern.add_nodes_from(["pair", "string", "array"])
    pattern.add_edges_from([
        ("pair", "string"),
        ("pair", "array")
    ])
    pattern.add_node_attrs("pair", {"type": "pair"})
    pattern.add_node_attrs("string", {"type": "string", "text": b"\"steps\""})
    pattern.add_node_attrs("array", {"type": "array"})

    instances = graph.find_matching(pattern)
    assert len(instances) == 1
    _id = instances[0]["array"]
    # graph.remove_node(next(graph.predecessors(_id)))
    for sb in graph.successors(_id):
        print(finiteset2json(graph.nodes()[sb]["text"]))
    # walk(graph)


if __name__ == "__main__":
    main()
