import collections
import csv
import pandas as pd
from regraph import NXGraph, Rule, FiniteSet
import json

from regraph.backends.networkx.plotting import plot_rule


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
    Gives a new name to the type of the node with the index "child_index", of the list of all the
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
    # print_graph(graph)
    # create_subgraph(graph, 10)
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
    # rule = Rule.from_transform(G)

    # print graph
    # print_graph(G)
    # subgraph = create_subgraph(G, 1)
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
            remove_descendants(G, pattern_type, instances)

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

    return G


def arrange_graph(G):
    # read json file
    f = open('knowledge_base/graph_clearing_patterns.json', "r")
    json_data = json.loads(f.read())

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
            try:
                G.add_edge(n, current_node_list[i + 1])
            except:
                pass
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
            # print(node_ids)
            for nested_function_call in json_data["nested_function_calls"][node]:
                for id in node_ids:
                    nested_function = (G.get_node(id))
                    if nested_function_call in nested_function:
                        nodes_to_refactor = (nested_function[nested_function_call])
                        i = 1
                        for node in nodes_to_refactor:
                            for j in nested_function["argument_list"]:
                                if node.decode("utf-8") in str(j):
                                    nested_function["argument_list"] = {}
                            node = node.decode("utf-8")
                            node_dict = {"type": "default", "label": node + "()", "caller_function": node, "parent_id": -1, "child_id": id}
                            new_node_id = id * 10 + i
                            i += 1
                            G.add_node(new_node_id, node_dict)
                            G.add_edge(new_node_id, id)

    # add other hyperparameter nodes
    for node in json_data["hyperparameters"]:
        hyperparameter_pattern = create_simple_pattern(node, node)
        instances = G.find_matching(hyperparameter_pattern)
        if len(instances) != 0:
            node_attribute = list(hyperparameter_pattern._graph.nodes._nodes)[0]
            node_ids = get_ids(node_attribute, instances)
            for node_attribute in json_data["hyperparameters"][node]:
                for id in node_ids:
                    node = (G.get_node(id))
                    node_clone = node
                    if node_attribute in node:
                        nodes_to_refactor = (node[node_attribute])
                        for n in nodes_to_refactor:
                            n = n.decode("utf-8")
                            n = n.replace("(", "").replace(")", "")
                            # split arguments in the argument list
                            splitted_list = n.split(", ")
                            nodes_to_refactor = splitted_list
                            node_clone.update({node_attribute: splitted_list})

                        i = 1
                        for node in nodes_to_refactor:
                            # node = node.decode("utf-8")
                            if "=" in node:
                                node_name, node_value = node.split("=")
                                node_dict = {"type": "input", "label": f'{node_name}={node_value}', "value": node_value,
                                             "parent_id": -1, "child_id": id}
                                new_node_id = id * 10 + i
                                i += 1
                                if node != "()":
                                    # print(node)
                                    G.add_node(new_node_id, node_dict)
                                    G.add_edge(new_node_id, id)
                    G.update_node_attrs(id, node_clone)
                    # else:
                    # node_name = node
                    # node_value = ""

    return G


def arrange_graph_v3(G):
    f = open('knowledge_base/graph_clearing_patterns.json', "r")
    json_data = json.loads(f.read())

    # remove module node
    G.remove_node(0)

    # delete all edges
    for edge in list(G.edges()):
        G.remove_edge(edge[0], edge[1])

    for node1_id in list(G.nodes()):
        node1 = G.get_node(node1_id)

        if "variable_list" in list(node1.keys()):
            # get the name of the variables as a list of strings
            variables = list(node1["variable_list"])[0].decode("utf-8").split(',')
            # clear whitespaces in the name of the variables
            variables = [var.strip() for var in variables]

            for node2_id in list(G.nodes()):
                node2 = G.get_node(node2_id)

                if "argument_list" in list(node2.keys()):

                    arguments = list(node2["argument_list"])[0].decode("utf-8").split(',')
                    arguments = [arg.strip() for arg in arguments]
                    # remove parenthesis of first argument
                    arguments[0] = arguments[0][1:]
                    # remove parenthesis of last argument
                    arguments[-1] = arguments[-1][:-1]

                    for var in variables:
                        if var in arguments and (node1_id, node2_id) not in list(G.edges()):
                            G.add_edge(node1_id, node2_id)

    new_node_id = max(list(G.nodes())) + 1
    for node in json_data["nested_function_calls"]:
        nested_calls = create_simple_pattern(node, node)
        instances = G.find_matching(nested_calls)
        if len(instances) != 0:
            node_type = list(nested_calls._graph.nodes._nodes)[0]
            node_ids = get_ids(node_type, instances)
            # print(node_ids)
            for nested_function_call in json_data["nested_function_calls"][node]:
                for id in node_ids:
                    nested_function = (G.get_node(id))
                    if nested_function_call in nested_function:
                        nodes_to_refactor = (nested_function[nested_function_call])
                        i = 1
                        for node in nodes_to_refactor:
                            for j in nested_function["argument_list"]:
                                if node.decode("utf-8") in str(j):
                                    nested_function["argument_list"] = {}
                            node = node.decode("utf-8")
                            node_dict = {"type": "default", "label": node + "()", "caller_function": node, "parent_id": -1, "child_id": id}
                            i += 1
                            G.add_node(new_node_id, node_dict)
                            G.add_edge(new_node_id, id)
                            new_node_id += 1

    for node1_id in list(G.nodes()):
        node1 = G.get_node(node1_id)

        if "caller_function" in list(node1.keys()):
            caller_func = list(node1["caller_function"])[0]

            if type(caller_func) == bytes:
                caller_func = caller_func.decode("utf-8")

            obj = caller_func.split('.')[0]

            for node2_id in list(G.nodes()):
                node2 = G.get_node(node2_id)

                if "variable_list" in list(node2.keys()):
                    variables = list(node2["variable_list"])[0].decode("utf-8").split(',')
                    variables = [var.strip() for var in variables]

                    if obj in variables:
                        G.add_edge(node2_id, node1_id)

        if "subscript_object" in list(node1.keys()):
            sub_obj = list(node1["subscript_object"])[0].decode("utf-8").split('.')[0]

            for node2_id in list(G.nodes()):
                node2 = G.get_node(node2_id)

                if "variable_list" in list(node2.keys()):
                    variables = list(node2["variable_list"])[0].decode("utf-8").split(',')
                    variables = [var.strip() for var in variables]

                    if sub_obj in variables:
                        G.add_edge(node2_id, node1_id)

    return G

def arrange_graph_v2(G):
    # remove module node
    G.remove_node(0)

    # delete all edges
    for edge in list(G.edges()):
        G.remove_edge(edge[0], edge[1])

    new_node_id = max(list(G.nodes())) + 1
    variable_ids = []

    # create new node for each variable in variable_list and add edge to expression_statement
    for node_id in list(G.nodes()):
        node = G.get_node(node_id)

        if "variable_list" in list(node.keys()):
            # get the name of the variables as a list of strings
            variables = list(node["variable_list"])[0].decode("utf-8").split(',')
            # clear whitespaces in the name of the variables
            variables = [var.strip() for var in variables]

            for var in variables:
                G.add_node(new_node_id, {"type": "variable", "label": var})
                G.add_edge(node_id, new_node_id)
                variable_ids.append(new_node_id)
                new_node_id += 1

    # search if there is a variable for each argument in argument_list, and if so, connect variable to
    # expression_statement
    for node1_id in list(G.nodes()):
        node1 = G.get_node(node1_id)

        if "argument_list" in list(node1.keys()):
            # convert argument_list into a list of strings
            arguments = list(node1["argument_list"])[0].decode("utf-8").split(',')
            # remove whitespaces
            arguments = [arg.strip() for arg in arguments]
            # remove parenthesis of first argument
            arguments[0] = arguments[0][1:]
            # remove parenthesis of last argument
            arguments[-1] = arguments[-1][:-1]

            for node2_id in list(G.nodes()):
                node2 = G.get_node(node2_id)

                if node2_id > node1_id and list(node2["type"])[0] == "variable":
                    if list(node2["label"])[0] in arguments:
                        G.add_edge(node2_id, node1_id)

    # create a node for each argument that is not a variable
    for node_id in list(G.nodes()):
        node = G.get_node(node_id)

        if "argument_list" in list(node.keys()):
            # convert argument_list into a list of strings
            arguments = list(node["argument_list"])[0].decode("utf-8").split(',')
            # remove whitespaces
            arguments = [arg.strip() for arg in arguments]
            # remove parenthesis of first argument
            arguments[0] = arguments[0][1:]
            # remove parenthesis of last argument
            arguments[-1] = arguments[-1][:-1]

            for arg in arguments:
                has_match = False
                for var_id in variable_ids:
                    var_node = G.get_node(var_id)

                    if arg == list(var_node["label"])[0]:
                        has_match = True

                if not has_match:
                    G.add_node(new_node_id, {"type": "argument", "label": arg})
                    G.add_edge(new_node_id, node_id)
                    new_node_id += 1

    return G


def rewrite_graph(G, language):
    # read data from knowledge base
    # print_graph(G)
    assert language != '', 'language is not set'
    if language in ['python', 'snakemake']:
        df = pd.read_csv("knowledge_base/signatures_p.csv")
        f = open('knowledge_base/rewrite_rules_p.json', "r")
    elif language == 'r':
        df = pd.read_csv("knowledge_base/signatures_r.csv")
        f = open('knowledge_base/rewrite_rules_r.json', "r")
    mapping = dict(zip(df.name, df.category))

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
                label_set = 0
                node_attributes = G.get_node(pattern_id).get(attr_type)
                # print(node_attributes)
                # compare each attribute text with signatures
                if bool(node_attributes) != 0:
                    for attribute_bytes in node_attributes:

                        if isinstance(attribute_bytes, (bytes, bytearray)):
                            attribute = attribute_bytes.decode("utf-8")
                        else:
                            attribute = attribute_bytes
                        dot = "."
                        if dot in attribute and language == "python":
                            attribute = trim(attribute)
                        for name in mapping:
                            new_attributes = G.get_node(pattern_id)
                            if attribute == name:
                                new_attributes["label"] = mapping[name]
                                G.update_node_attrs(pattern_id, new_attributes)
                                print(attribute)
                                label_set = 1
                                break
                            else:
                                if language == 'python':
                                    new_label = new_attributes["caller_function"]
                                    new_attributes["label"] = new_label
                                    G.update_node_attrs(pattern_id, new_attributes)
                        if label_set == 0:
                            new_label = new_attributes["text"]
                            new_attributes["label"] = new_label
                            G.update_node_attrs(pattern_id, new_attributes)

                            # new_attributes["type"] = "operator"


    # print_graph(G)
    rule = Rule.from_transform(G)
    # plot_rule(rule)
    return G


def jsonify_finite_set(param):
    if len(param.to_json()["data"]) > 1:
        result_list = list()
        for element in param.to_json()["data"]:
            if isinstance(element, (bytes, bytearray)):
                result_list.append(element.decode("utf-8"))
            else:
                result_list.append(element)
        return result_list
    data = param.to_json()["data"][0]
    if isinstance(data, (bytes, bytearray)):
        data = data.decode("utf-8")
    return data


def convert_graph_to_json(G):
    print_graph(G)
    graph_dict = {"nodes": [], "edges": []}
    for n, attrs in G.nodes(data=True):
        # print(attrs["type"])
        if str(attrs["type"]) == "{'input'}":
            metadata = {"id": str(n), "type": "input", "targetPosition": "top", "position": {"x": 0, "y": 0},
                        "data": {}}
        else:
            metadata = {"id": str(n), "type": "default", "targetPosition": "top", "position": {"x": 0, "y": 0},
                        "data": {}}
        # node_attrs = {}
        node_raw_attrs = G.get_node(n)
        for key in node_raw_attrs:
            metadata["data"].update({key: jsonify_finite_set(node_raw_attrs[key])})

        # node_attrs.update(G.get_node(n))
        graph_data = {}
        graph_dict["nodes"].append(metadata)
        # graph_dict["nodes"].append(graph_data)
    i = 1
    for s, t, attrs in G.edges(data=True):
        edge_id = "edge-" + str(i)
        edge_attrs = {"id": edge_id, "source": str(s), "target": str(t), 'type': 'smoothstep'}
        graph_dict["edges"].append(edge_attrs)
        i += 1
    # print(graph_dict)
    with open('graph.json', 'w') as fp:
        json.dump(graph_dict, fp, indent=4)
    return graph_dict
