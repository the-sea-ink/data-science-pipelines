from collections import defaultdict
from astpretty import pprint
from astunparse import unparse
from typing import Optional, List, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
import ast
import sys


class DefaultDict(defaultdict):
    def __missing__(self, key):
        return key


mapping = {
    'print': 'user_output',
    'fit': 'model_training',
    'predict': 'model_prediction',
    'fit_predict': 'model_prediction',
    'fit_transform': 'data_transformation_fit',
    # '': '',
}

class ASTVisitor:
    class __ASTVisitor(ast.NodeVisitor):
        def __init__(self):
            self.assigns = defaultdict(dict)
            self.deps = DefaultDict()
            self.calls = dict()
            self.aliases = DefaultDict()
            self.catalog = defaultdict(lambda: "UNKNOWN")
            for k, v in mapping.items():
                self.catalog[k] = v
            signatures = pd.read_csv('data/signatures.csv')
            for k, v in zip(signatures['long_name'], signatures['category']):
                self.catalog[k] = v

            self.targets = []
            self.values = []
            self.args = []

        def __flatten(self, collection):
            for item in collection:
                if isinstance(item, list):
                    for subc in self.__flatten(item): yield subc
                else: yield item

        def visit_Import(self, node):
            for alias in node.names:
                short = alias.name if alias.asname is None else alias.asname
                self.aliases[short] = alias.name
            return node

        def visit_ImportFrom(self, node):
            for alias in node.names:
                short = alias.name if alias.asname is None else alias.asname
                self.aliases[short] = ".".join([node.module, alias.name])
            return node

        def visit_Constant(self, node):
            self.deps[(node.lineno, node.col_offset)] = f'{node.value}::{type(node.value).__name__}'
            self.generic_visit(node)

        def visit_Name(self, node):
            self.deps[(node.lineno, node.col_offset)] = node.id
            self.generic_visit(node)

        def visit_Assign(self, node):
            # pprint(node)
            self.values.append(type(node.value).__name__)
            for el in node.targets:
                self.targets.append(type(el).__name__)

                key = (node.value.lineno, node.value.col_offset)
                if isinstance(el, ast.Name):
                    self.assigns[el.id][(el.lineno, el.col_offset)] = key
                elif isinstance(el, ast.Tuple):
                    if hasattr(node.value, 'elts'):
                        for t, v in zip(el.elts, node.value.elts):
                            self.assigns[t.id][(t.lineno, t.col_offset)] = (v.lineno, v.col_offset)
                    else:
                        for e in el.elts:
                            self.assigns[e.id][(e.lineno, e.col_offset)] = key 
                elif isinstance(el, (ast.Subscript, ast.Attribute)):
                    pprint(el)
                    self.assigns[el.value.id][(el.value.lineno, el.value.col_offset)] = key
                else:
                    print(type(el))
                    print(unparse(node))
            self.generic_visit(node)

        def __unfold_alias(self, name):
            modules = name.split('.')
            return (name
                    if len(modules) == 1
                    else ".".join([self.aliases[modules[0]]] + modules[1:]))

        def __get_rec_attr(self, node):
            return (node.id
                    if isinstance(node, ast.Name)
                    else (".".join([self.__get_rec_attr(node.value), node.attr])
                          if isinstance(node, ast.Attribute)
                          else "UNKNOWN-NEITHER-NAME-NOR-ATTR"))

        def visit_Tuple(self, node):
            # pprint(node)
            for arg in node.elts:
                self.args.append(type(arg).__name__)
            args = [(idx, arg.lineno, arg.col_offset)
                    for idx, arg in enumerate(node.elts)]
            self.calls[(node.lineno, node.col_offset)] = ('tuple', 'UNKNOWN', None, args)
            self.generic_visit(node)

        def visit_List(self, node):
            # pprint(node)
            for arg in node.elts:
                self.args.append(type(arg).__name__)
            args = [(idx, arg.lineno, arg.col_offset)
                    for idx, arg in enumerate(node.elts)]
            self.calls[(node.lineno, node.col_offset)] = ('list', 'UNKNOWN', None, args)
            self.generic_visit(node)

        def visit_Dict(self, node):
            # pprint(node)
            for arg in node.values:
                self.args.append(type(arg).__name__)
            args = [(idx.value, arg.lineno, arg.col_offset)
                    for idx, arg in zip(node.keys, node.values)]
            self.calls[(node.lineno, node.col_offset)] = ('dict', 'UNKNOWN', None, args)
            self.generic_visit(node)

        def visit_BinOp(self, node):
            # pprint(node)
            self.calls[(node.lineno, node.col_offset)] = (type(node.op).__name__, 'UNKNOWN', None, [(0, node.left.lineno, node.left.col_offset), (1, node.right.lineno, node.right.col_offset)])
            self.generic_visit(node)

        def visit_Call(self, node):
            # pprint(node)
            func = self.__get_rec_attr(node.func)
            mark = self.catalog[self.aliases[self.__unfold_alias(func)]].upper()
            asg = None
            for k, vv in self.assigns.items():
                if asg:
                    break
                for i, v in vv.items():
                    if v == (node.lineno, node.col_offset):
                        asg = i
                        break
            for arg in node.args:
                self.args.append(type(arg).__name__)
            args = [(idx, arg.lineno, arg.col_offset)
                    for idx, arg in enumerate(node.args)]
            args += [(kw.arg, kw.value.lineno, kw.value.col_offset)
                     for kw in node.keywords]
            if isinstance(node.func, ast.Attribute):
                if func.split('.')[0] in self.assigns:
                    args = [(-1, node.func.lineno, node.func.col_offset)] + args

            name = self.__unfold_alias(func)
            self.calls[(node.lineno, node.col_offset)] = (name, mark, asg, args)
            self.generic_visit(node)

        # def resolve_deps(self, deps):
        #     # print(deps)
        #     res = []
        #     for it in deps:
        #         # if isinstance(it, str):
        #         r = self.deps[(it[1], it[2])]
        #         res.append((it[0], r if isinstance(r, str) else self.resolve_deps(self.calls[r][-1])))
        #     return res

        def __assign_exists(self, key):
            for k, vv in self.assigns.items():
                for i, v in vv.items():
                    if i == key:
                        return True
            return False

        def visit_Subscript(self, node):
            # pprint(node)
            if isinstance(node.ctx, ast.Store):
                return node
            else:
                asg = None
                for k, vv in self.assigns.items():
                    if asg:
                        break
                    for i, v in vv.items():
                        if v == (node.lineno, node.col_offset):
                            asg = i
                            break
                deps = [node.value.id] + [n.id
                        for n in ast.walk(node.slice) if isinstance(n, ast.Name)]
                for k, vv in self.assigns.items():
                    for i, v in vv.items():
                        print(k, i, v)
                deps = [(idx, list(self.assigns[dep].keys())[0][0], list(self.assigns[dep].keys())[0][1]) for idx, dep in enumerate(deps) if dep in self.assigns]
                # used_vars = list(self.__flatten(self.assigns.values()))
                # deps = [node.value.id] + [var for var in set(deps) if var in used_vars]
                if asg == 'no_assignment': asg = 'slice'
                key = (node.lineno, node.col_offset)
                self.calls[key] = ('slice', 'DATA_PROJECTION', asg, deps)
                self.generic_visit(node)

    instance = None

    def __init__(self):
        # if not ASTVisitor.instance:
        ASTVisitor.instance = ASTVisitor.__ASTVisitor()

    def __getattr__(self, name):
        return getattr(self.instance, name)


def node_exists(nodes, name):
    return len([n for n in nodes if n['id'] == name]) == 1

def graph(inspector):
    nodes, edges, asgs = [], [], {}
    yfactor = 40
    keys = list(inspector.calls.keys())
    idx = 1
    while keys:
        key = keys.pop(0)
        name, mark, asg, args = inspector.calls[key]
        # if mark == "UNKNOWN":
        #     continue
        print(key, name, mark, asg, args)
        nodes.append({
                'id': f'{key[0]}-{key[1]}',
                'data': {
                    'label': f'{name}',
                },
                'position': { 'x': np.random.randint(400), 'y': yfactor * key[0] },
            })

        if asg:
            var = None
            for k, vv in inspector.assigns.items():
                if var:
                    break
                for i, v in vv.items():
                    if i == asg:
                        var = k
                        break
            asgs[var] = key

            edges.append({
                'id': f'{asg[0]}-{asg[1]}-{key[0]}-{key[1]}',
                'source': f'{key[0]}-{key[1]}',
                'type': 'smoothstep',
                'sourcePosition': str(idx),
                'target': f'{asg[0]}-{asg[1]}',
            })

        for arg in args:
            idx, lineno, offset = arg
            k = (lineno, offset)
            var = inspector.deps[k]
            if var == k:
                var = inspector.calls[k]

            print(var)
            if isinstance(var, tuple):
                tmp = inspector.calls[k]
                inspector.calls[k] = ('tuple', 'UNKNOWN', key, tmp[3])
                keys.append(k)
            else:
                if var not in inspector.assigns:
                # if not node_exists(nodes, f'{lineno}-{offset}'):
                #     if var not in asgs.keys():
                    nodes.append({
                        'id': f'{lineno}-{offset}',
                        'data': {
                            'label': f'{var}',
                        },
                        'position': { 'x': np.random.randint(400), 'y': yfactor * (lineno-2) },
                    })
                    # else:
                        # k = asgs[var]

                    edges.append({
                        'id': f'{var}-{k[0]}-{k[1]}-{name}-{key[0]}-{key[1]}',
                        'source': f'{k[0]}-{k[1]}',
                        'type': 'smoothstep',
                        'sourcePosition': str(idx),
                        'target': f'{key[0]}-{key[1]}',
                    })

                else:
                    k = [v for i, v in inspector.assigns[var].items()][0]
                    print(var, list(inspector.assigns[var].items()))
                    edges.append({
                        'id': f'{var}-{k[0]}-{k[1]}-{name}-{key[0]}-{key[1]}',
                        'source': f'{k[0]}-{k[1]}',
                        'type': 'smoothstep',
                        'sourcePosition': str(idx),
                        'target': f'{key[0]}-{key[1]}',
                    })                    


    return nodes, edges


def parse(code):
    tree = ast.parse(code)

    inspector = ASTVisitor()
    inspector.visit(tree)

    for k, v in inspector.assigns.items():
        print(k, v)

    nodes, edges = graph(inspector)
    return nodes, edges


def main():
    code = open('sklearn_example.py').read()
    # print(code)
    parse(code)


if __name__ == "__main__":
    main()
