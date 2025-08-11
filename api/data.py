from __future__       import annotations

import logging
import pandas as pd

from typing           import List
from datasets         import load_dataset
from typing           import List
from models.document import Document
from utils.config   import DATASET_LANG, DATASET_SIZE, WIKIPEDIA_DATES

logger = logging.getLogger(__name__)


def load_wikipedia_docs(limit: int = DATASET_SIZE) -> List[Document]:
    """
    Load up to `limit` PT-BR wikipedia docs using Hugging Face datasets.
    """
    dataset = None
    # New canonical dataset is hosted on the Hub as "wikimedia/wikipedia"
    for date in WIKIPEDIA_DATES:
        cfg = f"{date}.{DATASET_LANG}"
        try:
            dataset = load_dataset(
                "wikimedia/wikipedia",
                cfg,
                split="train",
                streaming=True,  # iterate without downloading the whole shard
            )
            logger.info("Loaded wikimedia/wikipedia dataset config=%s", cfg)
            break
        except Exception as e:  # pragma: no cover - network path
            logger.warning("Failed to load wikimedia/wikipedia %s: %s", cfg, e)


    # Convert to pandas and extract title + text
    items = []
    count = 0
    for i, row in enumerate(dataset):
        if i >= limit:
            break
        # IterableDataset yields dict rows
        title = row.get("title") if isinstance(row, dict) else None
        text = row.get("text") if isinstance(row, dict) else None
        if not text:
            continue
        # Sanitize newlines for small snippets later
        text_s = str(text).replace("\r", " ").replace("\n\n", "\n")
        items.append((i, title, text_s))
        count += 1

    df = pd.DataFrame(items, columns=["id", "title", "text"])
    docs = [Document(id=int(r.id), title=r.title, text=str(r.text)) for r in df.itertuples()]
    logger.info("Prepared %d wikipedia docs (requested %d)", len(docs), limit)
    return docs