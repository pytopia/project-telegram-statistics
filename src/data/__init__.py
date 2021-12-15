from pathlib import Path


DATA_DIR_ABSOLUTE = Path(__file__).resolve().parent
DATA_DIR = DATA_DIR_ABSOLUTE.relative_to(DATA_DIR_ABSOLUTE.parents[1])
