from typing import List

from api.utils.inference import InferenceUtils, Message


def test_format_messages_with_messages():
    messages = [Message(role="user", content="Bonjour"), Message(role="assistant", content="Salut")]
    out = InferenceUtils.format_messages(prompt=None, input=None, history=None, messages=messages)
    assert out == [
        {"role": "user", "content": "Bonjour"},
        {"role": "assistant", "content": "Salut"},
    ]


def test_format_messages_with_prompt_input_history():
    history = [Message(role="assistant", content="h1"), Message(role="developer", content="d1")]
    out = InferenceUtils.format_messages(prompt="sys", input="u1", history=history, messages=None)
    assert out == [
        {"role": "system", "content": "sys"},
        {"role": "assistant", "content": "h1"},
        {"role": "system", "content": "d1"},
        {"role": "user", "content": "u1"},
    ]


def test_format_embeddings_openai():
    inputs: List[str] = ["a", "b"]
    data = [
        {"object": "embedding", "embedding": [0.1, 0.2]},
        {"object": "embedding", "embedding": [0.3, 0.4]},
    ]
    out = InferenceUtils.format_embeddings_openai(inputs, data, model="test-model")
    assert out["object"] == "list"
    assert out["model"] == "test-model"
    assert len(out["data"]) == 2
    assert out["data"][0]["object"] == "embedding"


def test_embedding_to_points_and_tuple():
    inputs: List[str] = ["x", "y"]
    data = [
        {"object": "embedding", "embedding": [1.0, 2.0]},
        {"object": "embedding", "embedding": [3.0, 4.0]},
    ]
    pts = InferenceUtils.embedding_to_points(inputs, data)
    assert len(pts) == 2
    assert pts[0]["payload"]["source_text"] == "x"

    ids, vectors, payloads = InferenceUtils.embedding_to_tuple(inputs, data)
    assert ids == [0, 1]
    assert payloads[1]["source_text"] == "y"
    assert vectors[0] == [1.0, 2.0]


