import os
from typing import List


def _csv_env(name: str, default: str) -> List[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


DATASET_LANG        = os.getenv("DATASET_LANG", "pt")
DATASET_SIZE        = int(os.getenv("DATASET_SIZE", "200"))
WIKIPEDIA_DATES     = _csv_env("WIKIPEDIA_DATES", "20231101")
MODEL_NAME          = os.getenv("MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
TOP_K_MAX           = int(os.getenv("TOP_K_MAX", "20"))
LEXICAL_CHAR_WEIGHT = float(os.getenv("LEXICAL_CHAR_WEIGHT", "0.4"))  # peso da similaridade char n-grams (0=desliga)

# Silencia avisos de cache de symlinks por padrão
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")