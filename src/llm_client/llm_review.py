import os
from dotenv import load_dotenv
from google import genai
from abc import ABC, abstractmethod

from .raw_llm_review import raw_review_file
from .utils import extract_json

def review_file(file_path: str) -> dict:
    raw_result = raw_review_file(file_path)
    return extract_json(raw_result)


class LLMReviewer(ABC):
    api_key: str
    model_name: str

    def __init__(self, api_key_var, model_name):
        load_dotenv()
        self.api_key = os.getenv(api_key_var)
        if not self.api_key:
            raise RuntimeError(f"{api_key_var} environment variable is not set")
        self.model_name = model_name

    @abstractmethod
    def _generate_prompt(self) -> str:
        pass

    def llm_review(self) -> str:
        prompt = self._generate_prompt()
        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        return response.text

    
