from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse

from parser import bfs_tree_traverser
from rule_executioner import *
from tree_sitter import Language, Parser


class Extractor:
    def __init__(self):
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

    def _parse(self, code: str, language: str):
        """
        Parses given code into a tree
        :param prog_language: code language
        :param code: code to parse
        :return: tree-sitter
        """
        parser = Parser()
        assert language != '', 'language is not set'
        self.language = language
        parser.set_language(Language('build/my-languages.so', language))
        tree = parser.parse(bytes(code, "utf8"))
        return tree

    def _get_graph(self, tree):
        nxgraph = bfs_tree_traverser(tree)

        # rewrite graph
        rename_graph_types(nxgraph, self.language)
        G = transform_graph(nxgraph)
        G = arrange_graph_v3(G)
        G = rewrite_graph(G, self.language)
        json_graph = convert_graph_to_json(G)
        return json_graph

    def produce(self, code: str, language: str):
        return self._get_graph(self._parse(code, language))


app = FastAPI()

jsons = Path('.')
frontend = Path('dist/')

@app.get("/")
async def root():
    return FileResponse(frontend / 'index.html')

@app.get("/main.js")
async def js():
    return FileResponse(frontend / 'main.js')

@app.get("/main.css")
async def css():
    return FileResponse(frontend / 'main.css')

@app.post("/upload")
async def upload_data(file: UploadFile = File(...), language: str = Form(...)):
    code = b''
    while content := await file.read(1024):  # async read chunk
        code += content  # async write chunk

    data = Extractor().produce(code.decode('utf-8'), language)
    # print(data)
    return {
        "type": "graph",
        "error": None,
        "values": {
            "code": code.decode('utf-8'),
            "nodes": data["nodes"],
            "edges": data["edges"],
        }
    }

@app.post("/update")
async def update_code(code: str = Form(...), language: str = Form(...)):
    data = Extractor().produce(code, language)
    # print(data)
    return {
        "type": "graph",
        "error": None,
        "values": {
            "code": code,
            "nodes": data["nodes"],
            "edges": data["edges"],
        }
    }
