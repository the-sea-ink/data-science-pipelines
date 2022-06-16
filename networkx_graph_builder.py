from pyparsing import unicode
from tree_sitter import Language, Parser
import networkx as nx
from regraph import NXGraph, Rule, plot_rule
import graph_tools as gt
import numpy
import pattern_builder


def parse(prog_language, code):
    """
    Parses given code into a tree
    :param prog_language: code language
    :param code: code to parse
    :return: tree-sitter
    """
    if prog_language != "python" and prog_language != "r":
        print("Currently only Python and R are supported.")
        return

    language = Language('./build/my-languages.so', prog_language)
    parser = Parser()
    parser.set_language(language)
    tree = parser.parse(bytes(code, "utf8"))
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
                G.add_node(node_id, attrs={"type": child_node.type, "text": child_node.text, "parent_id": parent_id})
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


def nx2gt(nxG):
    """
    Converts a networkx graph to a graph-tool graph.
    """
    # Phase 0: Create a directed or undirected graph-tool Graph
    gtG = gt.Graph(directed=nxG.is_directed())

    # Add the Graph properties as "internal properties"
    for key, value in nxG.graph.items():
        # Convert the value and key into a type for graph-tool
        tname, value, key = get_prop_type(value, key)

        prop = gtG.new_graph_property(tname)  # Create the PropertyMap
        gtG.graph_properties[key] = prop  # Set the PropertyMap
        gtG.graph_properties[key] = value  # Set the actual value

    # Phase 1: Add the vertex and edge property maps
    # Go through all nodes and edges and add seen properties
    # Add the node properties first
    nprops = set()  # cache keys to only add properties once
    for node, data in nxG.nodes(data=True):

        # Go through all the properties if not seen and add them.
        for key, val in data.items():
            if key in nprops: continue  # Skip properties already added

            # Convert the value and key into a type for graph-tool
            tname, _, key = get_prop_type(val, key)

            prop = gtG.new_vertex_property(tname)  # Create the PropertyMap
            gtG.vertex_properties[key] = prop  # Set the PropertyMap

            # Add the key to the already seen properties
            nprops.add(key)

    # Also add the node id: in NetworkX a node can be any hashable type, but
    # in graph-tool node are defined as indices. So we capture any strings
    # in a special PropertyMap called 'id' -- modify as needed!
    gtG.vertex_properties['id'] = gtG.new_vertex_property('string')

    # Add the edge properties second
    eprops = set()  # cache keys to only add properties once
    for src, dst, data in nxG.edges_iter(data=True):

        # Go through all the edge properties if not seen and add them.
        for key, val in data.items():
            if key in eprops: continue  # Skip properties already added

            # Convert the value and key into a type for graph-tool
            tname, _, key = get_prop_type(val, key)

            prop = gtG.new_edge_property(tname)  # Create the PropertyMap
            gtG.edge_properties[key] = prop  # Set the PropertyMap

            # Add the key to the already seen properties
            eprops.add(key)

    # Phase 2: Actually add all the nodes and vertices with their properties
    # Add the nodes
    vertices = {}  # vertex mapping for tracking edges later
    for node, data in nxG.nodes(data=True):

        # Create the vertex and annotate for our edges later
        v = gtG.add_vertex()
        vertices[node] = v

        # Set the vertex properties, not forgetting the id property
        data['id'] = str(node)
        for key, value in data.items():
            gtG.vp[key][v] = value  # vp is short for vertex_properties

    # Add the edges
    for src, dst, data in nxG.edges_iter(data=True):

        # Look up the vertex structs from our vertices mapping and add edge.
        e = gtG.add_edge(vertices[src], vertices[dst])

        # Add the edge properties
        for key, value in data.items():
            gtG.ep[key][e] = value  # ep is short for edge_properties

    # Done, finally!
    return gtG


def find_pattern():
    return


def match_pattern():
    return


# read code
code1 = """
import numpy as np
n_success = 0
print("Python is great!")
"""

code2 = """
import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
X, y = make_classification(random_state=0)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)
pipe = Pipeline([('scaler', StandardScaler()), ('svc', SVC())])
# The pipeline can be used as any other estimator
# and avoids leaking the test set into the train set
pipe.fit(X_train, y_train)
pipe.score(X_test, y_test)
"""

code = """
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
dataset = pd.read_csv('../input/Position_Salaries.csv')
X = dataset.iloc[:, 1:2].values
y = dataset.iloc[:, -1].values
from sklearn.preprocessing import StandardScaler
sc_X = StandardScaler()
sc_Y = StandardScaler()
X = sc_X.fit_transform(X)
y = np.squeeze(sc_Y.fit_transform(y.reshape(-1, 1)))
# the feature scaling will be done to both X and Y and still Y will remain the Vector
from sklearn.svm import SVR
regressor = SVR(kernel = 'rbf')
regressor.fit(X, y)
SVR(C=1.0, cache_size=200, coef0=0.0, degree=3, epsilon=0.1,
    gamma='auto_deprecated', kernel='rbf', max_iter=-1, shrinking=True,
    tol=0.001, verbose=False)
y_pred = regressor.predict([[6.5]])
y_pred = sc_Y.inverse_transform(y_pred)
print(y_pred)
"""

# source: https://www.kaggle.com/code/monkeyorman/simple-linear-regression-in-r-0-0648835
rcode = """
library(ggplot2) # Data visualization
library(readr) # CSV file I/O, e.g. the read_csv function
library(sqldf)
list.files("../input")
print('Total runtime is ~2 mins')
print('Importing train_2016 ... should be 90275')
train_2016 <- read_csv("../input/train_2016_v2.csv", col_types = cols(transactiondate = col_skip(), parcelid = col_integer())); nrow(train_2016)
print('Combining dupes (taking average) ... should be 90150')
train_2016 <- sqldf('SELECT parcelid, avg(logerror) as logerror FROM train_2016 GROUP BY parcelid'); nrow(train_2016)
print('Importing properties_2016 ... should be 2,985,217')
properties_2016 <- read_csv("../input/properties_2016.csv", col_types = cols(parcelid = col_integer())); nrow(properties_2016)
print('Combining train_2016 and properties_2016 ... should be 2,985,217')
#alldata <- sqldf("SELECT * FROM properties_2016 LEFT JOIN train_2016 USING(parcelid)"); nrow(alldata)
alldata <- merge(x = properties_2016, y = train_2016, by = "parcelid", all.x = TRUE)
print('Building model ...')
lr1 <- lm(logerror ~ fullbathcnt + calculatedfinishedsquarefeet + parcelid, data=alldata);
summary(lr1) # view the model
print('Making predictions ...')
predictions <- data.frame(predict(lr1, alldata))
print('Appending predictions to alldata ...')
alldata$p_lr1 <- predictions$predict.lr1..alldata.
alldata$p_lr1[is.na(alldata$p_lr1)] <- mean(alldata$logerror, na.rm = TRUE)  # Replace missing with average
print('Average prediction value is ...')
mean(alldata$p_lr1)
print('Creating submission file')
submit <- data.frame(alldata[,c("parcelid", "p_lr1")])
              submit$"201610" <- round(submit$p_lr1,4)
              submit$"201611" <- round(submit$p_lr1,4)
              submit$"201612" <- round(submit$p_lr1,4)
              submit$"201710" <- 0
              submit$"201711" <- 0
              submit$"201712" <- 0
submit$p_lr1<- NULL # remove the original prediction from the submit file
write.csv(submit, file = "submit_1.csv", row.names = FALSE, na="") # export the file for submission
print('Done!')
"""

#with open("bernoulli.py", "rb") as file:
 #   code += file.read()  # async read chunk
  #  code = code.decode('utf-8')

# parse code -> get tree-sitter
#tree_sitter = parse('python', code)
tree_sitter= parse('r', rcode)


# traverse tree-sitter -> get NXGraph
nxgraph = bfs_tree_traverser(tree_sitter)

# rewrite graph
G = pattern_builder.clear_graph(nxgraph)
G = pattern_builder.rewrite_graph(G)

# convert NXGraph -> get nx.Graph
#graph = convert_nxgraph_to_graph(nxgraph)

# nx.Graph -> gt.Graph, WiP
# gtG = nx2gt(graph)



