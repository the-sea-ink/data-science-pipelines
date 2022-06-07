from tree_sitter import Language, Parser

# example change

Language.build_library(
  # Store the library in the `build` directory
  'build/my-languages.so',

  # Include one or more languages
  [
    'tree-sitter-r',
    'tree-sitter-python',
    'tree-sitter-json'
  ]
)
