from abc import ABC, abstractmethod
from typing import List
from tree_sitter_languages import get_parser
from tree_sitter import Tree, Node

from .lang_utils import detect_language, SupportedLang


ROOT_AST_NODE_TYPE = [
    "module",
]


class SemanticASTNode:
    ast_node: Node
    children: List["SemanticASTNode"] = []
    parent: "SemanticASTNode"
    is_source_code_context: bool = False

    def __init__(self, ast_node: Node):
        self.ast_node = ast_node
        self.children = []
        self.parent = None

    @property
    def id(self) -> int:
        return self.ast_node.id

    def __eq__(self, value) -> bool:
        if not isinstance(value, SemanticASTNode):
            return False
        return self.id == value.id
    
    def __str__(self):
        return str(self.ast_node)
    
    def stringify(self, indent: str ="") -> str:
        if self.is_source_code_context:
            return self.ast_node.text.decode("utf-8", errors="replace")
        
        return str(self.ast_node) + "\n.....\n" + "\n".join(
            child.stringify(indent + "\t") + "\n....."
            for child in self.children
        )


class SemanticAST:
    path: str
    root: SemanticASTNode = None

    def __init__(self, path: str):
        self.path = path

    def stringify(self):
        if self.root is None:
            return ""
        return self.root.stringify()


class SourceCodeContextExpander(ABC):
    ast: Tree
    semantic_ast: SemanticAST

    def __init__(self, path, tree):
        super().__init__()
        self.semantic_ast = SemanticAST(path)
        self.ast = tree

    def _find_path_to_deepest_node_at_line(self, node: Node, line: int) -> List[Node]:
        if not (node.start_point[0] <= line <= node.end_point[0]):
            return None

        for child in node.children:
            child_path = self._find_path_to_deepest_node_at_line(child, line)
            if child_path:
                return [node] + child_path

        return [node]

    @abstractmethod
    def _find_shortest_semantic_path(self, deepest_path: List[Node]) -> List[Node]:
        pass

    def _find_shortest_semantic_path_to_line(self, line: int) -> List[Node]:
        deepest_path = self._find_path_to_deepest_node_at_line(
            self.ast.root_node, line)
        if deepest_path is None:
            raise ValueError(f"Line {line} is outside the source file range")
        return self._find_shortest_semantic_path(deepest_path)

    def _find_shortest_semantic_path_to_tuple(self, lines: tuple) -> List[List[Node]]:
        if len(lines) != 2:
            raise ValueError(
                f"Length of a tuple element in request lines must be 2, not {len(lines)}")

        upper_path = self._find_shortest_semantic_path_to_line(lines[0])
        lower_path = self._find_shortest_semantic_path_to_line(lines[1])

        expr_paths: List[List[Node]] = []
        if upper_path[-1].id == lower_path[-1].id:
            expr_paths.append(upper_path)
        else:
            expr_paths.append(upper_path)
            expr_paths.append(lower_path)

        return expr_paths

    def _append_path_to_semantic_ast(self, path: List[Node]):
        cur_node = self.semantic_ast.root
        for i, node in enumerate(path):
            if node.id == cur_node.id:
                continue
            next_node = SemanticASTNode(node)
            if next_node in cur_node.children:
                continue

            cur_node.children.append(next_node)
            next_node.parent = cur_node
            cur_node = next_node
            if i == len(path) - 1:
                next_node.is_source_code_context = True

    def _construct_semantic_ast(self, expr_paths: List[List[Node]]):
        for path in expr_paths:
            if path[0].type not in ROOT_AST_NODE_TYPE:
                raise ValueError(
                    "The root of semantic path must be a root AST node")

            if self.semantic_ast.root is None:
                self.semantic_ast.root = SemanticASTNode(path[0])

            self._append_path_to_semantic_ast(path)

    def expand_source_code_context(self, request_lines: List[int | tuple]) -> SemanticAST:
        expr_paths: List[List[Node]] = []
        for request in request_lines:
            if isinstance(request, int):
                expr_paths.append(self._find_shortest_semantic_path_to_line(
                    line=request))
            elif isinstance(request, tuple):
                expr_paths.extend(self._find_shortest_semantic_path_to_tuple(
                    lines=request))
            else:
                raise ValueError(f"Unsupported request value {type(request)}")

        self._construct_semantic_ast(expr_paths)
        return self.semantic_ast


def get_source_code_context_expander(path: str, content: str) -> SourceCodeContextExpander:
    '''
    Get the appropriate SourceCodeContextExpander based on the programming language.
    '''
    language = detect_language(path)

    if language == SupportedLang.PYTHON:
        parser = get_parser(SupportedLang.PYTHON.value)
        tree = parser.parse(content.encode('utf-8'))

        from .ast_python import PythonSourceContextExpander
        return PythonSourceContextExpander(path, tree)
    # Add more languages as needed
    else:
        raise NotImplementedError(
            f"Source code {path} context expander for language '{language.value}' is not implemented.")

def ast_based_expand_context(path: str, content: str, request_lines: List[int | tuple] = [0]) -> SemanticAST:
    lang = detect_language(path)
    if lang == SupportedLang.UNKNOWN:
        return None
    expander = get_source_code_context_expander(path, content)
    return expander.expand_source_code_context(request_lines)
