from git import Repo
import re
from typing import List

'''
For each diff from python git library, we extract necessary information and store in MiniDiff object
For each MiniDiff, we further extract diff hunks and store in MiniDiffHunk objects
'''


class MiniDiffHunk:
    old_start_line: int
    old_end_line: int
    new_start_line: int
    new_end_line: int
    hunk_content: str


class MiniDiff:
    change_type: str
    old_path: str
    new_path: str
    diff_hunks: List[MiniDiffHunk]
    diff_content: str
    old_content: str

    def __init__(self):
        self.diff_hunks = []
        self.change_type = None
        self.old_path = None
        self.new_path = None
        self.diff_content = ""
        self.old_content = ""

    def __str__(self):
        return f"DIFF from {self.old_path} to {self.new_path}:\n{self.diff_content}"


class DiffExtractor:
    _repo: Repo
    _diffs: List[MiniDiff]

    def __init__(self, repo_path: str):
        self._repo = Repo(repo_path)
        self._diffs = []

    def get_diffs(self) -> List[MiniDiff]:
        return self._diffs

    def get_repo(self) -> Repo:
        return self._repo

    def _parse_diff_hunks(self):
        '''
        Parse diff content to extract hunks
        '''
        # Get lines starting with @@
        pattern = re.compile(
            r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", re.MULTILINE)

        for diff in self._diffs:
            content = diff.diff_content

            matches = list(pattern.finditer(content))

            for i, match in enumerate(matches):
                hunk = MiniDiffHunk()

                # Get hunk position info
                hunk.old_start_line = int(match.group(1))
                hunk.new_start_line = int(match.group(3))

                old_count = int(match.group(2)) if match.group(2) else 1
                new_count = int(match.group(4)) if match.group(4) else 1
                hunk.old_end_line = hunk.old_start_line + old_count - 1
                hunk.new_end_line = hunk.new_start_line + new_count - 1

                # Get hunk content from current @@ to next @@ or EOF
                start_index = match.start()
                if i < len(matches) - 1:
                    end_index = matches[i+1].start()
                else:
                    end_index = len(content)

                # Slice the hunk content
                hunk.hunk_content = content[start_index:end_index].strip()

                diff.diff_hunks.append(hunk)

    def extract_diffs(self, target_branch: str, base_branch: str) -> List[MiniDiff]:
        '''
        Extract diffs between target_branch and base_branch, these diffs represent for a pull request
        '''
        target_head = self._repo.commit(target_branch)
        base_head = self._repo.commit(base_branch)

        merge_bases = self._repo.merge_base(target_head, base_head)
        if not merge_bases:
            raise ValueError(f"No common ancestor found between {target_branch} and {base_branch}")
        merge_base = merge_bases[0]

        # Get raw diffs first to capture change types
        # Because diffs from diff(create_patch=True) currently leads change_type to None
        raw_diffs = merge_base.diff(target_head)
        change_type_map = {
            (diff.a_path, diff.b_path): diff.change_type 
            for diff in raw_diffs
        }
        # Get diffs with patch content
        diffs = merge_base.diff(target_head, create_patch=True)

        for i, diff in enumerate(diffs):
            mini_diff = MiniDiff()
            mini_diff.change_type = change_type_map.get(
                (diff.a_path, diff.b_path), None
            )
            mini_diff.old_path = diff.a_path
            mini_diff.new_path = diff.b_path
            mini_diff.diff_content = diff.diff.decode("utf-8", errors="replace")

            blob = merge_base.tree[diff.a_path] if diff.a_path else None
            mini_diff.old_content = blob.data_stream.read().decode("utf-8") if blob else ""

            self._diffs.append(mini_diff)

        # Parse diff to get hunks
        self._parse_diff_hunks()

        return self._diffs
