from typing import List
import logging

from .diff_extractor import DiffExtractor, MiniDiff
from ..semantic_ast.ast_file_analysis import ast_based_expand_context, SemanticAST

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class KudoDiff:
    change_type: str
    old_path: str
    new_path: str
    diff_content: str
    old_content: str
    semantic_ast: SemanticAST = None

    def __init__(self, mini_diff: MiniDiff):
        self.change_type = mini_diff.change_type
        self.old_path = mini_diff.old_path
        self.new_path = mini_diff.new_path
        self.diff_content = mini_diff.diff_content

    def __str__(self):
        return f"Diff (change_type={self.change_type}, old_path={self.old_path}, new_path={self.new_path}, \n Diffs = \n {self.diff_content})"

    def get_source_code_context(self) -> str:
        if self.old_path is not None:
            source = f"=== {self.old_path} === \n"
        else:
            source = f"=== Add new file {self.new_path} === \n"

        if self.semantic_ast is None:
            return source + self.old_content
        else:
            return source + self.semantic_ast.stringify()


class DiffAnalyzer:
    _repo_path: str
    raw_diffs: List[MiniDiff]
    kudo_diffs: List[KudoDiff]

    def __init__(self, repo_path: str):
        self._repo_path = repo_path
        self.kudo_diffs = []

    def _expand_context(self, mini_diffs: List[MiniDiff]):
        for mini_diff in mini_diffs:
            lines: List[int | tuple] = []
            for hunk in mini_diff.diff_hunks:
                hunk_tuple = (hunk.old_start_line - 1, hunk.old_end_line - 1)
                lines.append(hunk_tuple)

            file_diff = KudoDiff(mini_diff=mini_diff)
            if not (mini_diff.old_path is None or mini_diff.new_path is None):
                semantic_ast = ast_based_expand_context(
                    mini_diff.old_path, mini_diff.old_content, lines)
                file_diff.semantic_ast = semantic_ast
            if file_diff.semantic_ast is None:
                file_diff.old_content = mini_diff.old_content

            self.kudo_diffs.append(file_diff)

    def analyze_diffs(self, target_branch: str, base_branch: str) -> List[KudoDiff]:
        # Extract diffs
        diff_extractor = DiffExtractor(self._repo_path)
        self.mini_diffs = diff_extractor.extract_diffs(target_branch, base_branch)
        # Expand source code context
        self._expand_context(self.mini_diffs)
        return self.kudo_diffs

    def get_source_code_context(self) -> str:
        return "".join(
            diff.get_source_code_context()
            for diff in self.kudo_diffs
        )
