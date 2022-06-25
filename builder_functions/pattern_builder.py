import collections
import csv
import pandas as pd
from regraph import NXGraph, Rule
import json


def remove_descendants(G, node_type, instances):
    removed_nodes = []
    for ins in instances:
        node_id = ins[node_type]
        # print(str(node_id) + ":")
        # handling nested function calls;
        # checking if we deleted a subgraph of a nested function yet
        if node_id not in removed_nodes:
            desc = G.descendants(node_id)
            # print(desc)
            for id in list(desc):
                G.remove_node(id)
                removed_nodes.append(id)
    return removed_nodes


def remove_nodes(G, ids):
    for id in ids:
        G.remove_node(id)
    return


def save_imports(G, node_ids):
    import_dict = []
    for id in node_ids:
        node_attributes = G.get_node(id)
        import_dict.append(node_attributes)
    return import_dict


# removes all the nodes and edges of all nodes in rule whose ids
# are not in the list
def remove_everything_else(ids, rule, num_nodes):
    for i in range(num_nodes):
        if i not in ids:
            rule.inject_remove_node(i)
    return rule


# gets the ids of all of the nodes of a certain "type" in an instance of a graph
def get_ids(node_type, instances):
    ids = []
    for instance in instances:
        node_id = instance[node_type]
        ids.append(node_id)
    return ids


# creates a pattern to filter a graph based on "node type"
# attr_name -> name given to the variable used to identify this node type
# node_type -> the type of node that wants to be filtered
def create_simple_pattern(attr_name, node_type):
    pattern = NXGraph()
    pattern.add_node(attr_name)
    pattern.add_node_attrs(attr_name, {"type": node_type})
    return pattern


# creates a subgraph of the nodes given in ids, searches for their descendants that match the different given patterns
# and adds the text attribute of nodes that match those patterns as an attribute to the ascendant node
def add_attrs_from_patterns(ids, patterns, is_import, G):
    """
    :param ids: parent IDs with important descendant nodes
    :param patterns: patterns of descendant nodes
    :param is_import:
    :param G: graph
    :return:
    """
    for id in ids:
        # if is_import else list(G.successors(id))
        subg_nodes = list(G.descendants(id))
        subg_nodes.append(id)
        subgraph = G.generate_subgraph(G, subg_nodes)
        # print_graph(subgraph)
        for pattern in patterns:
            instances = subgraph.find_matching(pattern)
            if len(instances) > 0:
                sub_id = get_ids(list(pattern._graph.nodes._nodes)[0], instances)
                # print(sub_id)
                for i in range(len(sub_id)):
                    node_attributes = {list(pattern._graph.nodes._nodes)[0]: subgraph.get_node(sub_id[i])["text"]}
                    # print(node_attributes)
                    G.add_node_attrs(id, attrs=node_attributes)


def create_subgraph(G, node_id):
    subg_nodes = list(G.descendants(node_id))
    subg_nodes.append(node_id)
    subgraph = G.generate_subgraph(G, subg_nodes)
    print_graph(subgraph)
    rule = Rule.from_transform(subgraph)
    # plot_rule(rule)
    return subgraph


def create_node_from_attr():
    return


# adds an edge between the parent of a node and all the children of that same node (grandparent - grandchildren
# connection) this is necessary in order to later be able to remove those nodes that only serve as connectors
def connect_parent_and_children(G, ids, rule):
    for id in ids:
        parent_id = list(G.predecessors(id))[0]
        for child_id in list(G.successors(id)):
            rule.inject_add_edge(parent_id, child_id)
    return rule


def print_graph(G):
    # print clear view of all nodes and their edges
    print("List of nodes: ")
    for n, attrs in G.nodes(data=True):
        print("\t", n, attrs)
    print()
    print("List of edges: ")
    for s, t, attrs in G.edges(data=True):
        print("\t{}->{}".format(s, t), attrs)


def rename_node_type(graph, all_instances, parent_type, child_index, old_type_name, new_type_name, which="="):
    """
    Gives a new name to the the type of the node with the index "child_index", of the list of all the
    children with the same node type.

    :params:
        - all_instances : instances returned from pattern matching a graph
        - parent_type : node type of the parent node
        - child_index : index of the child node that wants to be changed. Ex: If a node has 4 children with the same node type
            "dotted_name", and you want to change the type for the first child, the index is 0. If you want to change the type
            of the fourth child, the index is 3.
        - old_type_name : the current name given to the node's type
        - new_type_name : the new name that will replace the current one
        - which : if which is "=" then only the child_index is changed, if it is "<" then all below the child_index are also changed,
            if it is ">" then all above the child_index are also changed.

    :return:
        - changed_nodes : list with the ids of the nodes that were affected by the name change
    """

    counter = 0
    last_parent_id = 0
    changed_nodes = []

    for instance in all_instances:

        if last_parent_id != instance[parent_type]:
            counter = 0

        if counter == child_index and which == "=":
            node_id = instance[old_type_name]
            node = graph.get_node(node_id)
            node["type"] = {new_type_name}
            changed_nodes.append(node_id)
        elif counter <= child_index and which == "<":
            node_id = instance[old_type_name]
            node = graph.get_node(node_id)
            node["type"] = {new_type_name}
            changed_nodes.append(node_id)
        elif counter >= child_index and which == ">":
            node_id = instance[old_type_name]
            node = graph.get_node(node_id)
            node["type"] = {new_type_name}
            changed_nodes.append(node_id)

        last_parent_id = instance[parent_type]
        counter += 1

    return changed_nodes


def create_linear_pattern(ordered_node_types):
    """
    Creates a linear pattern. We call a linear pattern a graph formation that only has parent-child edges and
    no siblings.
    :params: ordered_node_types -> is a list with the node types in the order that the edges should be created
                in the pattern. Ex: [x, y, z] will create these 3 nodes and the edges [(x, y), (y,z)]
    """
    pattern = NXGraph()
    pattern.add_nodes_from(ordered_node_types)

    for i, node_type in enumerate(ordered_node_types):
        pattern.add_node_attrs(node_type, {"type": node_type})

        if ((i + 1) < len(ordered_node_types)):
            pattern.add_edge(ordered_node_types[i], ordered_node_types[i + 1])

    return pattern


def sort_instances(all_instances, last_node_type):
    """
    Sorts all the instances, by the index of the last node's type. Since the initial parsed tree is traversed using
    breadth-first-search, by sorting by the last index in the tree you are also sorting the indexes of all the other
    node's types.
    """
    return sorted(all_instances, key=lambda x: (x[last_node_type]))


def print_nodes(graph, node_ids):
    for id in node_ids:
        print(graph.get_node(id))


def renaming_pipeline(graph, ordered_node_types, old_type_name, new_type_name, child_index, which="="):
    first_node = ordered_node_types[0]
    pattern = create_linear_pattern(ordered_node_types)
    all_instances = graph.find_matching(pattern)
    sorted_instances = sort_instances(all_instances, old_type_name)
    changed_nodes = rename_node_type(graph, sorted_instances, first_node, child_index, old_type_name, new_type_name,
                                     which)
    return changed_nodes


def trim(attribute):
    pos = attribute.find(".")
    attribute = attribute[pos + 1:]
    return attribute


def rename_graph_types(graph, language):
    if language != "python":
        return
    #print_graph(graph)
    # create_subgraph(graph, 13)
    f = open('knowledge_base/graph_clearing_patterns.json', "r")
    json_data = json.loads(f.read())
    changed_nodes = []

    for new_type in json_data["renaming_patterns"]:
        for patt in json_data["renaming_patterns"][new_type]:
            patt_data = json_data["renaming_patterns"][new_type][patt]
            linear_pattern = patt_data["linear_pattern"]
            old_type_name = patt_data["old_type_name"]
            new_type_name = patt_data["new_type_name"]
            child_index = patt_data["child_index"]
            which = patt_data["which"]

            changed_nodes.extend(
                renaming_pipeline(graph, linear_pattern, old_type_name, new_type_name, child_index, which))

    return list(set(changed_nodes))


def clear_graph(G):
    # create rule
    rule = Rule.from_transform(G)

    # print graph
    #print_graph(G)
    #subgraph = create_subgraph(G, 1)
    # print_graph(subgraph)

    # read json file
    f = open('knowledge_base/graph_clearing_patterns.json', "r")
    json_data = json.loads(f.read())

    # handle redundancies
    redundant_patterns = []
    for key in json_data["redundancies"]:
        value = json_data["redundancies"][key]
        pattern = create_simple_pattern(key, value)
        redundant_patterns.append(pattern)
    i = 0
    redundant_ids = []
    for pattern in redundant_patterns:
        instances = G.find_matching(pattern)
        if len(instances) != 0:
            pattern_name = list(redundant_patterns[i]._graph.nodes._nodes)[0]
            redundant_id = get_ids(pattern_name, instances)
            redundant_ids += redundant_id
        i += 1
    remove_nodes(G, redundant_ids)

    # handle nodes with descendants that contain necessary attributes
    for node in json_data["nodes_with_descendants"]:
        # find parent node
        parent_pattern = create_simple_pattern(node, node)
        instances = G.find_matching(parent_pattern)

        # get ids of all parent occurrences in the graph
        if len(instances) != 0:
            parent_type = list(parent_pattern._graph.nodes._nodes)[0]
            # print(parent_type)
            parent_ids = get_ids(parent_type, instances)

            # find its children names in json
            descendants_patterns = []
            for descendant_node in json_data["nodes_with_descendants"][node]:
                descendant_pattern = create_simple_pattern(descendant_node, descendant_node)
                descendants_patterns.append(descendant_pattern)

            # get attributes of children
            add_attrs_from_patterns(parent_ids, descendants_patterns, True, G)

            # clear descendants
            remove_descendants(G, parent_type, instances)

    # handle simple nodes
    for node in json_data["simple_nodes"]:
        pattern = create_simple_pattern(json_data["simple_nodes"][node], json_data["simple_nodes"][node])
        instances = G.find_matching(pattern)
        if len(instances) != 0:
            pattern_type = list(pattern._graph.nodes._nodes)[0]
            remove_descendants(G, pattern_type, instances, rule)

    # handle comments
    for node in json_data["nodes_to_completely_remove"]:
        patterns_to_remove = create_simple_pattern(node, node)
        instances = G.find_matching(patterns_to_remove)
        if len(instances) != 0:
            node_type = list(patterns_to_remove._graph.nodes._nodes)[0]
            node_ids = get_ids(node_type, instances)
            remove_nodes(G, node_ids)
    import_dict = []
    for node in json_data["import_save"]:
        imports_to_save = create_simple_pattern(node, node)
        instances = G.find_matching(imports_to_save)
        if len(instances) != 0:
            node_type = list(imports_to_save._graph.nodes._nodes)[0]
            node_ids = get_ids(node_type, instances)
            import_dict.append(save_imports(G, node_ids))
            remove_nodes(G, node_ids)

    # rearrange initially present nodes
    G.remove_node(0)
    current_node_list = []
    for n, attr in G.nodes(data=True):
        current_node_list.append(int(n))
    i = 0
    parent_id = 0
    for n in current_node_list:
        node_attrs = G.get_node(n)
        if n != current_node_list[-1]:
            G.add_edge(n, current_node_list[i + 1])
            node_attrs["child_id"] = current_node_list[i + 1]
            i += 1
        if parent_id != 0:
            node_attrs.update({"parent_id": parent_id})
        else:
            node_attrs.update({"parent_id": -1})
        G.update_node_attrs(n, node_attrs)
        parent_id = n

    # add nodes from nested functions
    for node in json_data["nested_function_calls"]:
        nested_calls = create_simple_pattern(node, node)
        instances = G.find_matching(nested_calls)
        if len(instances) != 0:
            node_type = list(nested_calls._graph.nodes._nodes)[0]
            node_ids = get_ids(node_type, instances)
            print(node_ids)
            for nested_function_call in json_data["nested_function_calls"][node]:
                print(nested_function_call)
                for id in node_ids:
                    nested_function = (G.get_node(id))
                    if nested_function_call in nested_function:
                        new_nodes = (nested_function[nested_function_call])
                        i = 1
                        for node in new_nodes:
                            node_dict = {"type": "call", "identifier": node, "parent_id" : -1 ,"child_id" : id}
                            new_node_id = id * 10 + i
                            i += 1
                            G.add_node(new_node_id, node_dict)
                            G.add_edge(new_node_id, id)

    return G


def rewrite_graph(G, language):
    # read data from knowledge base
    # print_graph(G)
    if language == 'python':
        df = pd.read_csv("knowledge_base/signatures_p.csv")
    elif language == 'r':
        df = pd.read_csv("knowledge_base/signatures_r.csv")
    mapping = dict(zip(df.name, df.category))

    # read json file
    if language == 'python':
        f = open('knowledge_base/rewrite_rules_p.json', "r")
    elif language == 'r':
        f = open('knowledge_base/rewrite_rules_r.json', "r")

    json_data = json.loads(f.read())

    variable_list = []

    # replace function calls
    for node in json_data:
        # print(node)
        # get one node type from the rewrite rules file
        pattern = create_simple_pattern(node, node)
        instances = G.find_matching(pattern)
        # For this specific node, find attribute type to read
        # acc. to rewrite rules
        attr_type = list(json_data[node].keys())[0]
        # print(attr_type)
        # print("---")
        # print(attr_type)
        # for this node type, find all graph nodes
        if len(instances) != 0:
            pattern_type = list(pattern._graph.nodes._nodes)[0]
            pattern_ids = get_ids(pattern_type, instances)
            # print(pattern_ids)
            # read attribute type for each node in pattern_ids
            for pattern_id in pattern_ids:
                node_attributes = G.get_node(pattern_id).get(attr_type)
                # print(node_attributes)
                # compare each attribute text with signatures
                if bool(node_attributes) != 0:
                    for attribute_bytes in node_attributes:
                        attribute = attribute_bytes.decode("utf-8")
                        dot = "."
                        if dot in attribute and language == "python":
                            attribute = trim(attribute)
                        for name in mapping:
                            if attribute == name:
                                new_attributes = G.get_node(pattern_id)
                                new_attributes["type"] = mapping[name]
                                G.update_node_attrs(pattern_id, new_attributes)

    # print_graph(G)
    return G


def arrange_graph(G):
    print_graph(G)
    return G
