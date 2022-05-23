from tree_sitter import Language, Parser

Language.build_library(
  # Store the library in the `build` directory
  'build/my-languages.so',

  # Include one or more languages
  [
    'tree-sitter-r',
    'tree-sitter-python'
  ]
)

R_LANGUAGE = Language('build/my-languages.so', 'r')
PY_LANGUAGE = Language('build/my-languages.so', 'python')


def walk(tree):
    def __walk(cursor, level=0):
        print(f'{"  "*level} {cursor.node.text.decode("utf-8")} ({cursor.node.type})')
        has_child = cursor.goto_first_child()
        if has_child:
            __walk(cursor, level+1)
            while cursor.goto_next_sibling():
                __walk(cursor, level+1)
            cursor.goto_parent()
        while cursor.goto_next_sibling():
            __walk(cursor, level)

    cursor = tree.walk()
    __walk(cursor)


parser = Parser()

parser.set_language(PY_LANGUAGE)

tree = parser.parse(bytes(open('example.py').read(), "utf8"))

walk(tree)

parser.set_language(R_LANGUAGE)

tree = parser.parse(bytes(open('example.r').read(), "utf8"))

walk(tree)
