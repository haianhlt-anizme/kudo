from enum import Enum

class SupportedLang(Enum):
    PYTHON = "python"
    UNKNOWN = "unknown"


def detect_language(file_path: str) -> SupportedLang:
    '''
    Detect the programming language of a file based on its extension.
    '''
    extension_to_language = {
        ".py": SupportedLang.PYTHON,
        # Add more mappings as needed
    }

    for ext, lang in extension_to_language.items():
        if file_path.endswith(ext):
            return lang
    return SupportedLang.UNKNOWN


