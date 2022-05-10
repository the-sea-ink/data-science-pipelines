from matplotlib import pyplot as plt
from collections import defaultdict
from collections import Counter
from dill.source import getname
from astunparse import unparse
from datetime import datetime
from inspect import signature
from astpretty import pprint
from pathlib import Path
from enum import Enum
import networkx as nx
import pandas as pd
import numpy as np
import contextlib
import pickle
import json
import time
import ast
import sys
import pwd
import os
import io


class DefaultDict(defaultdict):
    def __missing__(self, key):
        return key


class ASTVisitor:
    class __ASTVisitor(ast.NodeVisitor):
        def __init__(self):
            self.structure = defaultdict(lambda: 'no_assignment')

        def visit_Assign(self, node):
            # pprint(node)
            for el in node.targets:
                if isinstance(el, ast.Name):
                    key = (node.value.lineno, node.value.col_offset)
                    self.structure[key] = str(el.id)
                elif isinstance(el, ast.Tuple):
                    if hasattr(node.value, 'elts'):
                        for t, v in zip(el.elts, node.value.elts):
                            self.structure[(v.lineno, v.col_offset)] = str(t.id)
                    else:
                        v, names = node.value, [str(i.id) for i in el.elts]
                        self.structure[(v.lineno, v.col_offset)] = names
                elif isinstance(el, ast.Attribute):
                    key = (node.value.lineno, node.value.col_offset)
                    self.structure[key] = str(unparse(el)).strip()
                elif isinstance(el, ast.Subscript):
                    key = (node.value.lineno, node.value.col_offset)
                    self.structure[key] = str(unparse(el)).strip()
                else:
                    print(type(el))
                    print(unparse(node))
                    # pprint(node)
            self.generic_visit(node)

        def __get_rec_attr(self, node):
            return (node.id
                    if isinstance(node, ast.Name)
                    else (".".join([self.__get_rec_attr(node.value), node.attr])
                          if isinstance(node, ast.Attribute)
                          else "UNKNOWN-NEITHER-NAME-NOR-ATTR"))

        # def visit_Call(self, node):
        #     # pprint(node)
        #     key = (node.lineno, node.col_offset)
        #     self.structure[key] = self.__get_rec_attr(node.func)
        #     self.generic_visit(node)

    instance = None

    def __init__(self):
        if not ASTVisitor.instance:
            ASTVisitor.instance = ASTVisitor.__ASTVisitor()

    def __getattr__(self, name):
        return getattr(self.instance, name)


class ASTTransformer:
    class __ASTTransformer(ast.NodeTransformer):
        def __init__(self, assigns):
            self.assigns = assigns
            self.calls = dict()
            self.aliases = DefaultDict()
            self.catalog = defaultdict(lambda: "UNKNOWN")
            self.catalog['print'] = "user_output"
            self.catalog['fit'] = "model_training"
            self.catalog['predict'] = "model_prediction"
            self.catalog['fit_predict'] = "model_prediction"
            self.catalog['fit_transform'] = "data_transformation_fit"
            signatures = pd.read_csv('data/signatures.csv')
            for k, v in zip(signatures['long_name'], signatures['category']):
                self.catalog[k] = v
            self.structure = list()

        def flatten(self, collection):
            for item in collection:
                if isinstance(item, list):
                    for subc in self.flatten(item): yield subc
                else: yield item

        def set(self, assigns):
            self.assigns = assigns

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

        def visit_Call(self, node):
            # pprint(node)
            func = self.__get_rec_attr(node.func)
            mark = self.catalog[self.aliases[self.__unfold_alias(func)]].upper()
            if mark == "UNKNOWN":
                mark = self.catalog[func.split('.')[-1]].upper()
            asg = self.assigns[(node.lineno, node.col_offset)]
            deps = [(n.lineno, n.col_offset, n.id)
                    for n in ast.walk(node.func) if isinstance(n, ast.Name)]
            deps += [(n.lineno, n.col_offset, n.id) for arg in node.args
                     for n in ast.walk(arg) if isinstance(n, ast.Name)]
            deps += [(n.lineno, n.col_offset, n.id)
                     for arg in node.keywords for n in ast.walk(arg)
                     if isinstance(n, ast.Name)]
            deps = [v for x, y, v in sorted(deps)]
            name = self.__unfold_alias(func)
            used_vars = list(self.flatten(self.assigns.values()))
            # basename = func.split('.')[0]
            # if basename in used_vars: deps.append(basename)
            # deps = [var for var in set(deps) if var in used_vars]
            if asg == 'no_assignment': asg = name
            self.calls[(node.lineno, node.col_offset)] = (name, mark, asg, deps)
            target_node = (ast.Str(s=asg) if not isinstance(asg, list)
                           else ast.List(
                               elts=list(map(lambda x: ast.Str(s=x), asg)),
                               ctx=ast.Load()))
            deps_node = ast.List(
                elts=list(map(lambda x: ast.Str(s=x), deps)),
                ctx=ast.Load())
            v_list = list(map(lambda x: ast.Tuple(
                elts=[ast.Str(s='__arg__'),
                      ast.Str(s=unparse(x).strip())],
                ctx=ast.Load()), node.args))
            kw_list = list(map(lambda x: ast.Tuple(
                elts=[ast.Str(s=x.arg),
                      ast.Str(s=unparse(x.value).strip())],
                ctx=ast.Load()), node.keywords))
            args_node = ast.List(elts=v_list + kw_list, ctx=ast.Load())
            meta_dict = ast.Dict(
                keys=[ast.Str(s='lineno'), ast.Str(s='col_offset'),
                      ast.Str(s='name'), ast.Str(s='target'),
                      ast.Str(s='deps'), ast.Str(s='args')],
                values=[ast.Num(n=node.lineno),
                        ast.Num(n=node.col_offset),
                        ast.Str(s=name),
                        target_node,
                        deps_node,
                        args_node])
            return ast.Call(
                lineno=node.lineno,
                func=ast.Attribute(
                    lineno=node.lineno,
                    value=ast.Call(
                        lineno=node.lineno,
                        func=ast.Name(id='ProxyAnalyzer', ctx=ast.Load()),
                        args=[ast.Str(s=mark)],
                        keywords=[]),
                    attr='get', ctx=ast.Load()),
                args=[meta_dict, self.generic_visit(node.func)]
                + [self.generic_visit(arg) for arg in node.args],
                keywords=[self.generic_visit(arg) for arg in node.keywords])

        def visit_Subscript(self, node):
            # pprint(node)
            # print(node.ctx)
            if isinstance(node.ctx, ast.Store):
                # print("true")
                return node
            else:
                asg = self.assigns[(node.lineno, node.col_offset)]
                deps = [(n.lineno, n.col_offset, n.id)
                        for n in ast.walk(node.slice) if isinstance(n, ast.Name)]
                # deps += [(n.lineno, n.col_offset, n.s)
                #         for n in ast.walk(node.slice) if isinstance(n, ast.Str)]
                # deps += [(n.lineno, n.col_offset, n.n)
                #         for n in ast.walk(node.slice) if isinstance(n, ast.Num)]
                deps = [v for x, y, v in sorted(deps)]
                used_vars = list(self.flatten(self.assigns.values()))
                deps = [node.value.id] + [var for var in set(deps) if var in used_vars]
                # if node.value.id not in deps: deps.append(node.value.id)
                if asg == 'no_assignment': asg = 'slice'
                key = (node.lineno, node.col_offset)
                self.calls[key] = ('slice', 'DATA_PROJECTION', asg, deps)
                target_node = (ast.Str(s=asg) if not isinstance(asg, list)
                               else ast.List(
                                   elts=list(map(lambda x: ast.Str(s=x), asg)),
                                   ctx=ast.Load()))
                deps_node = ast.List(
                    elts=list(map(lambda x: ast.Str(s=x), deps)),
                    ctx=ast.Load())
                args_node = ast.Str(s=unparse(node.slice).strip())
                meta_dict = ast.Dict(
                    keys=[ast.Str(s='lineno'), ast.Str(s='col_offset'),
                          ast.Str(s='name'), ast.Str(s='target'),
                          ast.Str(s='deps'), ast.Str(s='args')],
                    values=[ast.Num(n=node.lineno),
                            ast.Num(n=node.col_offset),
                            ast.Str(s='slice'),
                            target_node,
                            deps_node,
                            args_node])
                return ast.Call(
                    lineno=node.lineno,
                    func=ast.Attribute(
                        lineno=node.lineno,
                        value=ast.Call(
                            lineno=node.lineno,
                            func=ast.Name(id='ProxyAnalyzer', ctx=ast.Load()),
                            args=[ast.Str(s='DATA_PROJECTION')],
                            keywords=[]),
                        attr='get', ctx=node.ctx),
                    args=[meta_dict, node], keywords=[])

    instance = None

    def __init__(self, assigns):
        if not ASTTransformer.instance:
            ASTTransformer.instance = ASTTransformer.__ASTTransformer(assigns)
        else:
            ASTTransformer.instance.set(assigns)

    def __getattr__(self, name):
        return getattr(self.instance, name)


class ProxyAnalyzer:
    class __ProxyAnalyzer:
        def __init__(self, mode):
            """proxy"""
            self.mode = mode
            self.__impl = defaultdict(lambda: GenericTracker().run)
            trackers = {
                "configuration": ConfigurationTracker().run,
                "data_loading": DataLoadingTracker().run,
                "data_projection": DataProjectionTracker().run,
                "data_splitting": DataSplittingTracker().run,
                "data_transformation": DataTransformationTracker().run,
                "data_transformation_fit": DataTransformationFitTracker().run,
                "model_declaration": ModelTracker().run,
                "model_training": ModelTrainingTracker().run,
                "model_selection": ModelSelectionTracker().run,
                "model_prediction": ModelPredictionTracker().run,
                "model_evaluation": ModelEvaluationTracker().run,
                "user_output": UserOutputTracker().run
            }
            for k, v in trackers.items(): self.__impl[k] = v
            signatures = pd.read_csv('data/signatures.csv')
            attributes = (pd.read_csv('data/attributes.csv')
                          .groupby('signature_id'))
            # .reset_index(drop=True)
            self.catalog = defaultdict(lambda: "UNKNOWN")
            self.sign_to_id = defaultdict(lambda: "UNKNOWN")
            for idx, item in signatures.iterrows():
                self.catalog[item['long_name']] = item['category']
                self.sign_to_id[item['name']] = item['id']
            self.attrs = defaultdict(lambda: "UNKNOWN")
            for name, group in attributes:
                group.sort_values(['att_order'], ascending = True)
                self.attrs[name] = dict([(name, {
                    "att_order": order,
                    "att_default": default,
                    "att_purpose": purpose
                }) for (_, _, order, name, default, purpose) in group.values])
            self.representation = dict()
            self.representation['experiment'] = {
                "experiment_id": 12345,
                "created_at": int(datetime.now().strftime("%Y%m%d%H%M%S")),
                "created_by": pwd.getpwuid(os.geteuid())[0],
                "data_ids": dict(),
                "ds_process": dict()
            }

        def get(self, meta, func, *args, **kwargs):
            mode = self.mode.lower()
            meta['attrs'] = self.attrs[self.sign_to_id[meta['deps'][0]]]
            # print(meta)
            # print(meta['lineno'])
            new_repr, res = self.__impl[mode](self.representation, func,
                                              meta, *args, **kwargs)
            self.representation = new_repr
            return res

        def set(self, mode): self.mode = mode

    instance = None

    def __init__(self, mode=None):
        if not ProxyAnalyzer.instance:
            ProxyAnalyzer.instance = ProxyAnalyzer.__ProxyAnalyzer(mode)
        else:
            ProxyAnalyzer.instance.set(mode)

    def __getattr__(self, name):
        return getattr(self.instance, name)


class Tracker:
    def __init__(self):
        pass

    def run(self, representation, func, meta, *args, **kwargs):
        return (representation, func(*args, **kwargs))


class GenericTracker(Tracker):
    def __init__(self):
        pass

    def run(self, representation, func, meta, *args, **kwargs):
        print(self.__class__.__name__, func.__name__)
        return (representation, func(*args, **kwargs))


class ConfigurationTracker(Tracker):
    def __init__(self):
        pass

    def run(self, representation, func, meta, *args, **kwargs):
        print(self.__class__.__name__, func.__name__)
        key = '%s_%d_%d' % ('config', meta['lineno'], meta['col_offset'])
        if 'env' not in representation['experiment']:
            representation['experiment']['env'] = dict()
        representation['experiment']['env'][key] = {
            "arg": meta['name'],
            "values": list(args)
        }
        return (representation, func(*args, **kwargs))


class DataFrameProfiler:
    def __init__(self):
        pass

    def on(self, data):
        self.profiles = dict()
        for idx, info in enumerate(zip(data.columns, data.dtypes)):
            col, dtype = info
            self.profiles[col] = {
                "column_id": idx,
                "column_name": col,
                "dtype": str(dtype)
            }
        return self


class DataLoadingTracker(Tracker):
    def __init__(self):
        pass
        # TODO: DataProfiler
        """
        "data": {
            "title": "data",
            "properties": {
                "dataset_id": { "type": "int" },
                "created_at": { "type": "float" },
                "created_by": { "type": "string" },
                "type": { "type": "string" },
                "name": { "type": "string" },
                "version": { "type": "string" },
                "source": { "type": "string" },
                "profile": { "type": "dict" },
                "__comment": "TODO: data profile, column profile",
                "__comment": "TODO: dataset id for data, X_train, X_test etc. what to put into the profile"
            },
            "required": "all",
            "description": "",
            "type": "object"
        },
        "data loading": {
            "title": "data loading",
            "properties": {
                "element_id": { "type": "int" },
                "prev_element_id": { "type": "int" },
                "code_block": { "type": "string" },
                "comments": { "type": "string" },
                "file_path": { "type": "string" },
                "dataset_id": { "type": "int" }
            }
        },
        """

    def run(self, representation, func, meta, *args, **kwargs):
        print(self.__class__.__name__, func.__name__)
        key = '%s_%d_%d' % ('data_loading', meta['lineno'], meta['col_offset'])
        if 'data' not in representation:
            representation['data'] = dict()
        did = int(str(meta['lineno']) + str(meta['col_offset']))
        data_key = '%s_%d' % ('data', did)
        representation['data'][data_key] = {
            "dataset_id": did,
            "created_at": int(datetime.now().strftime("%Y%m%d%H%M%S")),
            "created_by": pwd.getpwuid(os.geteuid())[0],
            # bug
            "type": 'local',
            "name": args[0].split('/')[-1],
            # bug
            "source": args[0],
            # bug
            "version": 1.0
        }
        data = func(*args, **kwargs)
        profiler = DataFrameProfiler().on(data)
        representation['data'][data_key]['profile'] = {
            "num_rows": int(data.shape[0]),
            "num_columns": int(data.shape[1])
        }
        if 'columns' not in representation['data'][data_key]['profile']:
            representation['data'][data_key]['profile']['columns'] = {}
        representation['data'][data_key]['profile']['columns'] = profiler.profiles
        representation['experiment']['data_ids'][key] = did
        representation['experiment']['ds_process'][key] = {
            "element_id": meta['target'],
            "pointer": '%d_%d' % (meta['lineno'], meta['col_offset']),
            "implementation": meta['name'],
            "prev_element_id": meta['deps'],
            "dataset_id": did,
            "file_path": args[0]
        }
        return (representation, data)


class DataTransformationFitTracker(Tracker):
    def __init__(self):
        pass

    def run(self, representation, func, meta, *args, **kwargs):
        print(self.__class__.__name__, func.__name__)
        key = '%s_%d_%d' % ('data_transformation', meta['lineno'], meta['col_offset'])

        tmp = sorted([k for k, v
                      in representation['experiment']['ds_process'].items()
                      if 'element_id' in v
                      and v['element_id'] == meta['deps'][0]])[-1]
        model_spec = representation['experiment']['ds_process'].pop(tmp)

        # print(meta['attrs'])
        # print(meta['args'])
        params = dict()
        if meta['attrs'] != "UNKNOWN":
            for k, param in enumerate(meta['attrs'].items()):
                # print(param)
                name, vals = param
                params['param_%d' % k] = {
                    "order": k,
                    "arg": name,
                    "value": vals['att_default'],
                    "by_default": vals['att_default']
                }
                if name.startswith('**'):
                    tmp = [{"keyword": key, "value": val} for key, val
                           in meta['args'] if key != '__arg__']
                    n = len(meta['args']) - len(tmp)
                    params['param_%d' % k]['value'] = tmp[k - n + 1:]
                elif name.startswith('*'):
                    tmp = [val for key, val in meta['args'] if key == '__arg__']
                    params['param_%d' % k]['value'] = tmp[k:]
                else:
                    if meta['args'][k][0] == '__arg__':
                        params['param_%d' % k]['value'] = meta['args'][k][-1]
                    else:
                        name, value = meta['args'][k]
                        params['param_%d' % k]['value'] = {
                            "keyword": name,
                            "value": value
                        }
        else:
            for k, (name, value) in enumerate(meta['args']):
                params['param_%d' % k] = {
                    "order": k,
                    "arg": name,
                    "value": value,
                    "by_default": "UNDEF"
                }

        model_spec['dataset_id'] = meta['deps'][1:]
        model_spec['args'] = params
        model_spec['pointer'] = '%d_%d' % (meta['lineno'], meta['col_offset'])
        model_spec['element_id'] = meta['target']
        model_spec['new_dataset_id'] = meta['target']
        model_spec['prev_element_id'].extend(meta['deps'][1:]),

        representation['experiment']['ds_process'][key] = model_spec
        return (representation, func(*args, **kwargs))


class DataTransformationTracker(Tracker):
    def __init__(self):
        pass

    def run(self, representation, func, meta, *args, **kwargs):
        print(self.__class__.__name__, func.__name__)
        key = '%s_%d_%d' % ('data_transformation', meta['lineno'], meta['col_offset'])
        params = dict()
        model = func(*args, **kwargs)
        for k, param in enumerate(signature(func).parameters.values()):
            default = param.default if param.default != param.empty else 'EMPTY'
            default = (default.__name__
                       if hasattr(default, '__name__')
                       else default)
            # print(k, param.name, default, param.kind)
            # val = getattr(model, param.name)
            # if hasattr(val, '__class__'): val = val.__class__
            # if hasattr(val, '__name__'): val = val.__name__
            params['param_%d' % k] = {
                "order": k,
                "arg": param.name,
                # "value": type(val).__name__,
                "value": default,
                "by_default": default
            }
        for k, param in enumerate(meta['args']):
            print(k, param)
            substr = "%s=" % params['param_%d' % k]['arg']
            res = param if not param.startswith(substr) else param[len(substr):]
            params['param_%d' % k]['value'] = res
        representation['experiment']['ds_process'][key] = {
            "element_id": meta['target'],
            "implementation": meta['deps'][0],
            "pointer": '%d_%d' % (meta['lineno'], meta['col_offset']),
            "prev_element_id": meta['deps'],
            "params": params
        }
        return (representation, model)


class DataProjectionTracker(Tracker):
    def __init__(self):
        pass
        """
        "data projection": {
            "title": "data projection",
            "properties": {
                "element_id": { "type": "int" },
                "prev_element_id": { "type": "int" },
                "code_block": { "type": "string" },
                "columns": { "type": "string" }
            }
        },
        """

    def run(self, representation, func, meta, *args, **kwargs):
        print(self.__class__.__name__, "SIZE: ", func.shape)
        key = '%s_%d_%d' % ('data_projection', meta['lineno'], meta['col_offset'])
        # BUG: indices, slices
        val = list(func) if isinstance(func, pd.DataFrame) else "unknown"
        representation['experiment']['ds_process'][key] = {
            "element_id": meta['target'],
            "pointer": '%d_%d' % (meta['lineno'], meta['col_offset']),
            "prev_element_id": meta['deps'],
            "columns": val,
            "dataset_id": meta['deps'][-1]
        }
        return (representation, func)


class DataSplittingTracker(Tracker):
    def __init__(self):
        pass
        """
        "data splitting": {
            "title": "data projection",
            "properties": {
                "element_id": { "type": "int" },
                "prev_element_id": { "type": "int" },
                "code_block": { "type": "string" },
                "mode": { "type": "string" },
                "ratio": { "type": "float" },
                "dataset_id": { "type": "int" },
                "new_dataset_id": { "type": "int" }
            }
        },
        """

    def run(self, representation, func, meta, *args, **kwargs):
        print(self.__class__.__name__, func.__name__)
        key = '%s_%d_%d' % ('data_splitting', meta['lineno'], meta['col_offset'])
        params = dict()

        # print(meta['attrs'])
        # print(meta['args'])
        params = dict()
        if meta['attrs'] != "UNKNOWN":
            for k, param in enumerate(meta['attrs'].items()):
                # print(param)
                name, vals = param
                params['param_%d' % k] = {
                    "order": k,
                    "arg": name,
                    "value": vals['att_default'],
                    "by_default": vals['att_default']
                }
                if name.startswith('**'):
                    tmp = [{"keyword": key, "value": val} for key, val
                           in meta['args'] if key != '__arg__']
                    n = len(meta['args']) - len(tmp)
                    params['param_%d' % k]['value'] = tmp[k - n + 1:]
                elif name.startswith('*'):
                    tmp = [val for key, val in meta['args'] if key == '__arg__']
                    params['param_%d' % k]['value'] = tmp[k:]
                else:
                    if meta['args'][k][0] == '__arg__':
                        params['param_%d' % k]['value'] = meta['args'][k][-1]
                    else:
                        name, value = meta['args'][k]
                        params['param_%d' % k]['value'] = {
                            "keyword": name,
                            "value": value
                        }
        else:
            for k, (name, value) in enumerate(meta['args']):
                params['param_%d' % k] = {
                    "order": k,
                    "arg": name,
                    "value": value,
                    "by_default": "UNDEF"
                }


        representation['experiment']['ds_process'][key] = {
            "element_id": meta['target'],
            "prev_element_id": meta['deps'][1:],
            "dataset_id": meta['deps'][1:],
            "new_dataset_ids": meta['target'],
            "implementation": meta['deps'][0],
            "params": params
        }
        return (representation, func(*args, **kwargs))


class ModelSelectionTracker(Tracker):
    def __init__(self):
        pass

    def run(self, representation, func, meta, *args, **kwargs):
        print(self.__class__.__name__, func.__name__)
        key = '%s_%d_%d' % ('model_selection', meta['lineno'], meta['col_offset'])
        params = dict()
        for k, param in enumerate(signature(func).parameters.values()):
            default = param.default if param.default != param.empty else 'EMPTY'
            default = (default.__name__
                       if hasattr(default, '__name__')
                       else default)
            # print(k, param.name, default, param.kind)
            params['param_%d' % k] = {
                "order": k,
                "arg": param.name,
                "value": default,
                "by_default": default
            }
        # print(meta)
        # for k, param in enumerate(args):
        #     print(type(param))
        #     print(k, param)
        for idx, param in enumerate(kwargs.items()):
            k, v = param
            # print(idx, k, v)
        for k, param in enumerate(meta['deps'][1:]):
            params['param_%d' % k]['value'] = param
        representation['experiment']['ds_process'][key] = {
            "element_id": meta['target'],
            "pointer": '%d_%d' % (meta['lineno'], meta['col_offset']),
            "prev_element_id": meta['deps'],
            "class": meta['deps'][0],
            "params": params
        }
        return (representation, func(*args, **kwargs))


class ModelTracker(Tracker):
    def __init__(self):
        pass

    def run(self, representation, func, meta, *args, **kwargs):
        print(self.__class__.__name__, func.__name__)
        key = '%s_%d_%d' % ('model_declaration',
                            meta['lineno'], meta['col_offset'])
        did = int(str(meta['lineno']) + str(meta['col_offset']))

        representation['experiment']['ds_process'][key] = {
            "element_id": meta['target'],
            "pointer": '%d_%d' % (meta['lineno'], meta['col_offset']),
            "implementation": meta['deps'][0],
            "prev_element_id": meta['deps'],
        }
        model = func(*args, **kwargs)

        params = dict()
        arct = dict()
        # print(meta['attrs'])
        # print(meta['args'])
        for idx, (name, param) in enumerate(signature(func).parameters.items()):
            # print(idx, name, param.name, param.default)
            default = (param.default
                       if param.default != param.empty
                       else 'EMPTY')
            default = (default.__name__
                       if hasattr(default, '__name__')
                       else default)
            params[name] = {
                "order": idx,
                "arg": name,
                "value": default,
                "by_default": default
            }
            if meta['attrs'] == "UNKNOWN":
                continue
            if name not in meta['attrs']:
                continue
            if meta['attrs'][name]['att_purpose'] == 'arct':
                params.pop(name)
                for step_id, step in enumerate(getattr(model, name)):
                    # print(step[1])
                    el_id = type(step[1]).__name__
                             # if hasattr(step[1], '__name__')
                             # else step[1])
                    arct['step_%d' % step_id] = {
                        "step_id": step_id,
                        "element_id": meta['deps'][step_id + 1],
                        "implementation": el_id,
                    }
                representation['experiment']['ds_process'][key]['architecture'] = arct
            elif meta['attrs'][name]['att_purpose'] == 'col_arct':
                params.pop(name)
                for step_id, step in enumerate(getattr(model, name)):
                    # print(name)
                    el_id = type(step[1]).__name__
                             # if hasattr(step[1], '__name__')
                             # else step[1])
                    arct['step_%d' % step_id] = {
                        "step_id": step_id,
                        "element_id": step[0],
                        "implementation": el_id,
                        "in_columns": step[2],
                    }
                representation['experiment']['ds_process'][key]['architecture'] = arct

        for idx, (arg, value) in enumerate(meta['args']):
            if arg not in params:
                continue
            if arg.startswith('**'):
                tmp = [{"keyword": key, "value": val} for key, val
                       in meta['args'] if key != '__arg__']
                n = len(meta['args']) - len(tmp)
                params[arg]['value'] = tmp[idx - n + 1:]
            elif arg.startswith('*'):
                tmp = [val for key, val in meta['args'] if key == '__arg__']
                params[arg]['value'] = tmp[idx:]
            else:
                if arg == '__arg__':
                    name = [key for key, val in params.items()
                            if val['order'] == idx][0]
                    params[name]['value'] = value
                else:
                    params[arg]['value'] = {
                        "keyword": arg,
                        "value": value
                    }

        representation['experiment']['ds_process'][key]['params'] = params
        # print(json.dumps(representation['experiment']['ds_process'][key],
        #                  indent=2, sort_keys=True))
        # print()
        return (representation, model)


class ModelTrainingTracker(Tracker):
    def __init__(self):
        pass

    def flatten(self, collection):
        for item in collection:
            if isinstance(item, list):
                for subc in self.flatten(item): yield subc
            else: yield item

    def __traverse_update(self, representation, element):
        if isinstance(representation, dict):
            for key in representation:
                if hasattr(representation[key], '__iter__'):
                    representation[key] = self.__traverse_update(
                        representation[key], element)
            if ('element_id' in representation
                and representation['element_id'] == element['element_id']):
                representation['implementation'] = element
            elif ('value' in representation
                  and representation['value'] == element['element_id']):
                representation['implementation'] = element
            # print(json.dumps(representation, indent=2, sort_keys=True))
        return representation

    def __rec_update(self, representation, meta, step=0):
        element = representation['experiment']['ds_process'][meta['key']]
        deps = element['prev_element_id']
        if step >= len(deps):
            return representation
        tmp = sorted([key for key, val
                      in representation['experiment']['ds_process'].items()
                      if key.startswith('model')
                      and 'element_id' in val
                      and val['element_id'] == deps[step]
                      and int(key.split('_')[-2]) <= meta['lineno']])
        # print(tmp)
        # print(deps)
        # print(deps[step])
        if len(tmp) > 0:
            model_spec = representation['experiment']['ds_process'].pop(tmp[-1])
            # print(model_spec)

            deps.pop(step)
            deps.insert(step, model_spec['prev_element_id'])


            element['prev_element_id'] = list(self.flatten(deps))
            element = self.__traverse_update(element, model_spec)
            # print(element)
            representation['experiment']['ds_process'][meta['key']] = element
        return self.__rec_update(representation, meta, step+1)

    def run(self, representation, func, meta, *args, **kwargs):
        print(self.__class__.__name__, func.__name__)
        meta['key'] = '%s_%d_%d' % ('model_training',
                                    meta['lineno'], meta['col_offset'])
        meta['did'] = int(str(meta['lineno']) + str(meta['col_offset']))
        model = func(*args, **kwargs)
        model_key = '%s_%d' % ('model', meta['did'])
        path = Path('./data') / 'models' / ('%s.pkl' % model_key)
        # print(model)
        pickle.dump(model, open(path, 'wb'))

        if 'model_ids' not in representation['experiment']:
            representation['experiment']['model_ids'] = dict()
        representation['experiment']['model_ids'][model_key] = meta['did']

        # representation['models'][model_key]['architecture'] = arct
        if 'models' not in representation['experiment']:
            representation['models'] = dict()

        representation['models'][model_key] = {
            "model_id": meta['did'],
            "created_at": int(datetime.now().strftime("%Y%m%d%H%M%S")),
            "created_by": pwd.getpwuid(os.geteuid())[0],
            "version": 1.0,
            "url": str(path)
        }

        representation['experiment']['ds_process'][meta['key']] = {
            "element_id": meta['target'],
            "pointer": '%d_%d' % (meta['lineno'], meta['col_offset']),
            "value": meta['deps'][0],
            "prev_element_id": meta['deps'],
        }

        new_repr = self.__rec_update(representation, meta)

        var = new_repr['experiment']['ds_process'][meta['key']]
        var['feature_dataset_id'] = meta['deps'][1]
        var['target_dataset_id'] = meta['deps'][2]
        var['model_id'] = meta['did']
        representation['models'][model_key]['implementation'] = var.pop('implementation', None)
        var.pop('value', None)
        new_repr['experiment']['ds_process'][meta['key']] = var

        return (new_repr, model)


class ModelPredictionTracker(Tracker):
    def __init__(self):
        pass

    def run(self, representation, func, meta, *args, **kwargs):
        print(self.__class__.__name__, func.__name__)
        key = '%s_%d_%d' % ('model_prediction', meta['lineno'], meta['col_offset'])
        representation['experiment']['ds_process'][key] = {
            "element_id": meta['target'],
            "pointer": '%d_%d' % (meta['lineno'], meta['col_offset']),
            "prev_element_id": meta['deps'],
            "dataset_id": meta['deps'][1:],
            "new_dataset_id": meta['target']
        }
        return (representation, func(*args, **kwargs))


class ModelEvaluationTracker(Tracker):
    def __init__(self):
        pass

    def run(self, representation, func, meta, *args, **kwargs):
        print(self.__class__.__name__, func.__name__)
        key = '%s_%d_%d' % ('model_evaluation', meta['lineno'], meta['col_offset'])
        res = func(*args, **kwargs)
        representation['experiment']['ds_process'][key] = {
            "element_id": meta['target'],
            "pointer": '%d_%d' % (meta['lineno'], meta['col_offset']),
            "prev_element_id": meta['deps'],
            "implementation": meta['deps'][0],
            "dataset_id": meta['deps'][1:],
            "value": res
        }
        return (representation, res)


class UserOutputTracker(Tracker):
    def __init__(self):
        pass

    def run(self, representation, func, meta, *args, **kwargs):
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            func(*args, **kwargs)
            _str = buf.getvalue()
        print(self.__class__.__name__, "CAPTURED OUTPUT: ", _str)
        key = '%s_%d_%d' % ('user_output', meta['lineno'], meta['col_offset'])
        representation['experiment']['ds_process'][key] = {
            "element_id": meta['target'],
            "pointer": '%d_%d' % (meta['lineno'], meta['col_offset']),
            "prev_element_id": meta['deps'][1:],
            "string": _str
        }
        return (representation, _str)


def plot_graph(transformer, _id):
    from networkx import DiGraph
    from networkx.drawing.nx_agraph import graphviz_layout

    dep_graph = DiGraph()
    mapping = {}
    to_filter = {
        "DATA_PROJECTION": lambda x: x[:1],
        "MODEL_TRAINING": lambda x: x[1:],
        "MODEL_PREDICTION": lambda x: x,
        "MODEL_EVALUATION": lambda x: x,
        "DATA_SPLITTING": lambda x: x[1:]
    }
    filtering = DefaultDict()
    for k, v in to_filter.items(): filtering[k] = v
    for k, v in transformer.calls.items():
        print(k, v)
        node = "%s_%d_%d" % (v[1], k[0], k[1])
        if v[1] != "MODEL_DECLARATION":
            mapping[node] = v[1]
            dep_graph.add_node(node)
            inputs = filtering[v[1]]
            inputs = inputs(v[-1]) if inputs != v[1] else v[-1]
            outputs = [v[-2]] if isinstance(v[-2], str) else v[-2]
            for element in inputs:
                if element == v[2]:
                    continue
                dep_graph.add_node(element)
                mapping[element] = element
                dep_graph.add_edge(element, node)
            for element in outputs:
                dep_graph.add_node(element)
                mapping[element] = element
                dep_graph.add_edge(node, element)
        else:
            for element in v[-1]:
                if element == v[2]:
                    continue
                dep_graph.add_node(element)
                mapping[element] = element
                dep_graph.add_edge(element, v[2])
    # pos = nx.circular_layout(dep_graph)
    pos = graphviz_layout(dep_graph, prog='dot')
    val_map = {'A': 1.0,
               'D': 0.5714285714285714,
               'H': 0.0}

    values = [val_map.get(node, 1) for node in dep_graph.nodes()]
    nx.draw_networkx_nodes(dep_graph, pos, cmap=plt.get_cmap('jet'),
                           node_color=values, node_size=10)
    nx.draw_networkx_labels(dep_graph, pos, mapping)
    nx.draw_networkx_edges(dep_graph, pos, edgelist=dep_graph.edges(),
                           edge_color='r', arrows=True)
    # plt.show()
    plt.savefig(f'fig_{_id}.png')



def main():
    tree = ast.parse(open('sklearn_example.py').read())

    inspector = ASTVisitor()
    inspector.visit(tree)

    # for k, v in inspector.structure.items():
    #     print(k, v)
    # print()

    tree_transformer = ASTTransformer(inspector.structure)
    tree = ast.fix_missing_locations(tree_transformer.visit(tree))
    print(unparse(tree))

    # for k, v in tree_transformer.aliases.items():
    #     print(k, v)

    # for k, v in tree_transformer.calls.items():
    #     print(k, v)

    # _id = int(datetime.now().strftime("%Y%m%d%H%M%S"))
    # plot_graph(tree_transformer, _id)
    #
    # exec(compile(tree, filename="<ast>", mode="exec"),
    #      {'ProxyAnalyzer': ProxyAnalyzer})
    #
    #
    # print(json.dumps(ProxyAnalyzer().representation, indent=2, sort_keys=True))
    # with open('data/representations/repr_%d.json' % _id, 'w') as f:
    #     json.dump(ProxyAnalyzer().representation, f)



if __name__ == "__main__":
    main()
