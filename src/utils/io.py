import json

def read_json(file_path: str) -> dict:
    """Reads a json file and returns the dict
    """
    with open(file_path) as f:
        return json.load(f)

def read_file(file_path: str) -> str:
    """Reads a file and returns the content
    """
    with open(file_path) as f:
        return f.read()
