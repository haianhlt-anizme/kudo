from .raw_llm_review import raw_review_file
from .utils import extract_json

def review_file(file_path: str) -> dict:
    raw_result = raw_review_file(file_path)
    return extract_json(raw_result)