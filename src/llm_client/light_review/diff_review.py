from typing import List

from ..llm_review import LLMReviewer
from ...diff.diff_analysis import DiffAnalyzer, KudoDiff


class DiffLightReviewer(LLMReviewer):
    kudo_diffs: List[KudoDiff]
    source_code_context: str
    response_scheme = """
{
    "state": "STOP | CONTINUE",
    "confidence": float in range (0-1),
    "request_review_funcs": [
        {
        "file": "string",
        "function": "string",
        "reason": "string"
        }
    ],
    "quick_review": [
        {
        "file": "string",
        "function": "string",
        "severity": "low | medium | high",
        "comment": "string"
        }
    ]
    }
"""

    def __init__(self, api_key_var, model_name, repo_path, base_branch, target_branch):
        super().__init__(api_key_var, model_name)
        diff_analyzer = DiffAnalyzer(repo_path=repo_path)
        self.kudo_diffs = diff_analyzer.analyze_diffs(
            target_branch=target_branch, base_branch=base_branch)
        self.source_code_context = diff_analyzer.get_source_code_context()

    def _generate_only_diff_prompt(self) -> str:
        diffs = "\n\n".join(
            f"--- Diff {i+1} ---\n{kd.diff_content}"
            for i, kd in enumerate(self.kudo_diffs)
        )

        return f"""
    You are a senior software engineer performing a lightweight code review.

    You are given ONLY git diffs.
    Do NOT assume any context outside the diffs.
    Only report issues that can be directly inferred from the changes.

    Your tasks:
    1. Decide whether this change needs deeper review.
    2. Identify functions, methods or files that likely require deeper inspection.
    3. Provide quick review comments based only on the diffs.

    Rules:
    - Be conservative when requesting deeper review.
    - If the change is trivial, mark state as STOP.

    Diffs:
    {diffs}

    Respond ONLY in valid JSON following the schema below.
    {self.response_scheme}
    """

    def _generate_diff_with_source_prompt(self) -> str:
        blocks = []

        for i, kd in enumerate(self.kudo_diffs):
            blocks.append(
                f"""
    --- Diff {i+1} ---
    {kd.diff_content}

    Relevant source context:
    {kd.get_source_code_context()}
    """
            )

        all_blocks = "\n".join(blocks)

        return f"""
    You are a senior software engineer reviewing code changes.

    You are provided with:
    1. Git diffs
    2. Partial source code context patched via tree-sitter, so you might see some parts like <Node ...>

    Your tasks:
    1. Decide whether this change needs deeper review.
    2. Identify functions, methods or files that likely require deeper inspection.
    3. Provide quick review comments based only on the diffs.

    IMPORTANT:
    - The source code context may contain "....." which represents omitted code.
    - Do NOT assume anything about omitted code.
    - Only report issues that can be directly inferred from the changes.

    Rules:
    - Be conservative when requesting deeper review.
    - If the change is trivial, mark state as STOP.

    Changes:
    {all_blocks}

    Respond ONLY in valid JSON following the schema below.
    {self.response_scheme}
    """

    def _generate_prompt(self) -> str:
        if len(self.source_code_context) > 500000:
            return self._generate_only_diff_prompt()
        else:
            return self._generate_diff_with_source_prompt()
