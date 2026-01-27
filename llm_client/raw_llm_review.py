import os
import json
from dotenv import load_dotenv
from google import genai


load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("GOOGLE_API_KEY environment variable is not set")
client = genai.Client(api_key=api_key)
model_name = "gemini-2.5-flash"


def generate_question(code: str) -> str:
    prompt = f"""
    You are a senior software engineer acting as a static code reviewer.

    OBJECTIVE:
    Analyze the given code and report ONLY findings that are directly supported by the code itself.

    DEFINITIONS:
    - Bug: A logic, syntax, or runtime error that will cause incorrect behavior.
    - Risk: A realistic scenario where this code could fail or be misleading in real usage.
    - Suggestion: A concrete improvement that improves correctness or clarity.

    SUMMARY RULES:
    - Provide a short, factual overall assessment of the code.
    - Do NOT include praise or vague statements.
    - Base the summary strictly on the findings below.
    - If the code is incorrect, state that clearly.

    STRICT RULES:
    - Do NOT speculate beyond the given code.
    - Do NOT invent context or usage.
    - If an issue cannot be proven from the code, do NOT include it.
    - If no issues exist for a category, return an empty array.

    OUTPUT FORMAT:
    Return ONLY valid JSON that strictly follows this schema:

    {{
    "summary": {{
        "overall_assessment": string,
        "confidence": "high | medium | low"
    }},
    "bugs": [
        {{
        "line": number,
        "type": "logic | syntax | runtime",
        "description": string
        }}
    ],
    "risks": [
        {{
        "description": string
        }}
    ],
    "suggestions": [
        {{
        "description": string
        }}
    ]
    }}

    CODE:
    {code}
    """
    return prompt


def generate_answer(prompt: str) -> str:
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )
    return response.text


def review_code(code: str) -> str:
    prompt = generate_question(code)
    answer = generate_answer(prompt)
    return answer


def raw_review_file(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as file:
        code = file.read()
    return review_code(code)