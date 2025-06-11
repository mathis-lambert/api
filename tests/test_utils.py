import pytest

from api.utils.inference import InferenceUtils, Message


def test_format_messages():
    history = [Message(role="user", content="hi"), Message(role="assistant", content="hello")]
    result = InferenceUtils.format_messages("sys", "question", history)
    assert result == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
        {"role": "user", "content": "question"},
    ]


def test_format_response():
    resp = InferenceUtils.format_response("answer", "job")
    assert resp == {"result": "answer", "job_id": "job"}


def test_embedding_helpers():
    inputs = ["a", "b"]
    data = [
        {"object": "embedding", "embedding": [1.0, 0.0]},
        {"object": "embedding", "embedding": [0.0, 1.0]},
    ]
    points = InferenceUtils.embedding_to_points(inputs, data)
    assert points[0]["payload"]["source_text"] == "a"

    ids, vectors, payloads = InferenceUtils.embedding_to_tuple(inputs, data)
    assert ids == [0, 1]
    assert vectors == [[1.0, 0.0], [0.0, 1.0]]
    assert payloads[1]["source_text"] == "b"

    formatted = InferenceUtils.format_embeddings(inputs, data, "job")
    assert formatted["job_id"] == "job"
    assert len(formatted["embeddings"]) == 2
