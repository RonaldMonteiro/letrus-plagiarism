import pytest

from match import topk_lexical, topk_semantic, build_index


def _toy_index():
    ids = [0, 1, 2]
    titles = ["A", "B", "C"]
    texts = [
        "O gato está no telhado. O gato mia alto.",
        "Cães são amigos do homem. Um cão late.",
        "Gatos e cães podem conviver em paz.",
    ]
    return build_index(ids, titles, texts)


@pytest.mark.slow
def test_topk_lexical_basic():
    idx = _toy_index()
    res = topk_lexical(idx, "gato no telhado", 2)
    assert len(res) == 2
    assert res[0][0] in {0, 2}


@pytest.mark.slow
def test_topk_semantic_basic():
    idx = _toy_index()
    res = topk_semantic(idx, "felino miando", 2)
    assert len(res) == 2