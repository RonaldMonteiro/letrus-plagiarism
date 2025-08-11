from main               import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health():
    request = client.get("/health")
    assert request.status_code == 200
    assert request.json()["status"] == "ok"


def test_compare_min():
    payload = {"text": "O café é uma bebida popular.", "top_k": 3}
    request = client.post("/compare", json=payload)
    assert request.status_code == 200
    data = request.json()
    assert "items" in data
    assert len(data["items"]) == 2
    for item in data["items"]:
        assert "method" in item
        assert "docs" in item
        assert isinstance(item["docs"], list)
        for doc in item["docs"]:
            assert "doc_id" in doc
            assert "sentences" in doc
            assert isinstance(doc["sentences"], list)
            for sent in doc["sentences"]:
                assert "doc_sentence" in sent
                assert "query_sentence" in sent
                assert "score" in sent