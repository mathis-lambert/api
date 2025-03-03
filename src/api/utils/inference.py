from typing import Dict, List, Tuple

from qdrant_client.models import PointStruct


class InferenceUtils:
    @staticmethod
    def format_messages(prompt: str, input: str, history: List) -> List:
        messages = []

        if prompt:
            messages.append({"role": "system", "content": prompt})

        if history:
            for entry in history:
                messages.append({"role": entry["role"], "content": entry["content"]})

        messages.append({"role": "user", "content": input})

        return messages

    @staticmethod
    def format_response(result: str, job_id: str) -> Dict:
        return {"result": result, "job_id": job_id}

    @staticmethod
    def format_embeddings(inputs: List[str], data: List[Dict], job_id: str) -> Dict:
        embeddings = [
            {
                "index": i,
                "embedding": embedding["embedding"],
                "payload": {"source_text": inputs[i]},
                "object": embedding["object"],
            }
            for i, embedding in enumerate(data)
            if embedding["object"] == "embedding"
        ]
        return {"embeddings": embeddings, "job_id": job_id}

    @staticmethod
    def embedding_to_points(inputs: List[str], data: List[Dict]) -> List[PointStruct]:
        points: List = [
            {
                "id": i,
                "vector": embedding["embedding"],
                "payload": {"source_text": inputs[i]},
            }
            for i, embedding in enumerate(data)
            if embedding["object"] == "embedding"
        ]
        return points

    @staticmethod
    def embedding_to_tuple(
        inputs: List[str], data: List[Dict]
    ) -> Tuple[List[int], List[List[float]], List[Dict]]:
        ids = []
        vectors = []
        payloads = []

        for i, embedding in enumerate(data):
            if embedding["object"] == "embedding":
                ids.append(i)
                vectors.append(embedding["embedding"])
                payloads.append({"source_text": inputs[i]})

        return ids, vectors, payloads
