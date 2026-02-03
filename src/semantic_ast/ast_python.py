from enum import Enum
from typing import List
from tree_sitter import Node

from .ast_file_analysis import SourceCodeContextExpander


class PythonMeaningfulAST(Enum):
    FUNC_DEF = "function_definition"
    CLASS_DEF = "class_definition"
    DECORATED_DEF = "decorated_definition"
    MODULE = "module"


MEANINGFUL_AST_TYPES = [
    PythonMeaningfulAST.DECORATED_DEF.value,
    PythonMeaningfulAST.CLASS_DEF.value,
    PythonMeaningfulAST.FUNC_DEF.value,
]


class PythonSourceContextExpander(SourceCodeContextExpander):
    def _refactor_semantic_path(self, node_path: List[Node]) -> List[Node]:
        if node_path[-1].type in [PythonMeaningfulAST.FUNC_DEF.value, 
                                  PythonMeaningfulAST.CLASS_DEF.value]:
            if node_path[-2].type == PythonMeaningfulAST.DECORATED_DEF.value:
                return node_path[0:-2]
        return node_path

    def _find_shortest_semantic_path(self, node_path: List[Node]) -> List[Node]:
        for i, node in reversed(list(enumerate(node_path))):
            if node.type in MEANINGFUL_AST_TYPES:
                node_path = node_path[0:i+1]
                break
            if node.type == PythonMeaningfulAST.MODULE.value:
                node_path = node_path[0:2]
        
        return self._refactor_semantic_path(node_path)
