import os
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, List

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

# Ensure the "api" package is imported from the src/ directory
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


from api.classes import Embeddings, TextGeneration  # noqa: E402
from api.main import app  # noqa: E402

# Import des mêmes symboles via le package pour s'assurer que la clé d'override correspond
from api.v1.security import (  # noqa: E402
    ensure_valid_api_key_or_token as _ensure_valid_api_key_or_token_pkg,
)
from api.v1.security import (
    get_current_user_with_api_key_or_token as _get_current_user_with_api_key_or_token_pkg,
)
from api.v1.security.api_auth import (  # noqa: E402
    ensure_valid_api_key_or_token as _ensure_valid_api_key_or_token,
)
from api.v1.security.api_auth import (
    get_current_user_with_api_key_or_token as _get_current_user_with_api_key_or_token,
)
from api.v1.services.get_classes import (
    get_embeddings as _get_embeddings_dep,  # noqa: E402
)
from api.v1.services.get_classes import (
    get_text_generation as _get_text_generation_dep,  # noqa: E402
)
from api.v1.services.get_databases import (  # noqa: E402
    get_mongo_client as _get_mongo_client_dep,
)
from api.v1.services.get_databases import (
    get_qdrant_client as _get_qdrant_client_dep,
)


class FakeMongoClientHandle:
    async def close(
        self
    ) -> None:  # compat avec await app.qdrant_client.get_client().close()
        return None


class FakeMongoConnector:
    def __init__(self):
        self._collections: Dict[str, List[Dict[str, Any]]] = {}

    def get_client(self):
        return FakeMongoClientHandle()

    def get_database(self):
        return self

    @staticmethod
    def serialize(document):
        if document is None:
            return None
        if "_id" in document and isinstance(document["_id"], ObjectId):
            document["_id"] = str(document["_id"])
        return document

    def _col(self, name: str) -> List[Dict[str, Any]]:
        return self._collections.setdefault(name, [])

    async def find_one(self, collection_name, query, projection=None):
        for doc in self._col(collection_name):
            ok = True
            for k, v in query.items():
                if doc.get(k) != v:
                    ok = False
                    break
            if ok:
                return doc.copy()
        return None

    async def find_many(self, collection_name, query, limit=100):
        results = []
        for doc in self._col(collection_name):
            ok = True
            for k, v in query.items():
                if doc.get(k) != v:
                    ok = False
                    break
            if ok:
                results.append(doc.copy())
            if len(results) >= limit:
                break
        return results

    async def insert_one(self, collection_name, document):
        if "_id" not in document:
            document["_id"] = ObjectId()
        self._col(collection_name).append(document.copy())
        return document["_id"]

    async def insert_many(self, collection_name, documents):
        ids = []
        for d in documents:
            if "_id" not in d:
                d["_id"] = ObjectId()
            self._col(collection_name).append(d.copy())
            ids.append(d["_id"])
        return ids

    async def update_one(self, collection_name, query, update):
        modified = 0
        for i, doc in enumerate(self._col(collection_name)):
            ok = True
            for k, v in query.items():
                if doc.get(k) != v:
                    ok = False
                    break
            if ok:
                if "$set" in update:
                    doc.update(update["$set"])
                else:
                    doc.update(update)
                self._collections[collection_name][i] = doc
                modified += 1
                break
        return modified

    async def update_many(self, collection_name, query, update):
        modified = 0
        for i, doc in enumerate(self._col(collection_name)):
            ok = True
            for k, v in query.items():
                if doc.get(k) != v:
                    ok = False
                    break
            if ok:
                if "$set" in update:
                    doc.update(update["$set"])
                else:
                    doc.update(update)
                self._collections[collection_name][i] = doc
                modified += 1
        return modified

    async def delete_one(self, collection_name, query):
        for i, doc in enumerate(self._col(collection_name)):
            ok = True
            for k, v in query.items():
                if doc.get(k) != v:
                    ok = False
                    break
            if ok:
                del self._collections[collection_name][i]
                return 1
        return 0

    async def delete_many(self, collection_name, query):
        deleted = 0
        keep = []
        for doc in self._col(collection_name):
            ok = True
            for k, v in query.items():
                if doc.get(k) != v:
                    ok = False
                    break
            if ok:
                deleted += 1
            else:
                keep.append(doc)
        self._collections[collection_name] = keep
        return deleted

    def object_id(self, id_str):
        return ObjectId(id_str)

    async def log_event(
        self, user_id: str, job_id: str, action: str, request_body: dict
    ):
        await self.insert_one(
            "events",
            {
                "user_id": ObjectId(user_id)
                if not isinstance(user_id, ObjectId)
                else user_id,
                "job_id": job_id,
                "action": action,
                "request_body": request_body,
            },
        )
        return True


class FakeQdrantClientHandle:
    async def close(self) -> None:
        return None


class FakeQdrantConnector:
    def __init__(self):
        self._collections: Dict[str, Dict[str, Any]] = {}

    def get_client(self):
        return FakeQdrantClientHandle()

    async def check_connection(self):
        return True

    async def create_collection(
        self, collection_name: str, vector_size: int = 1024, distance: str = "Cosine"
    ):
        if collection_name in self._collections:
            return True
        self._collections[collection_name] = {
            "name": collection_name,
            "vector_size": vector_size,
            "distance": distance,
            "vectors": [],
        }
        return True

    async def get_collection(self, collection_name: str):
        return self._collections.get(collection_name, None)

    async def search_in_collection(
        self, collection_name: str, query_vector: List[float], limit: int = 5
    ) -> List[dict]:
        # Renvoie une liste vide par défaut (aucune donnée indexée dans ce fake)
        return []


class FakeProvider:
    pass


TEST_USER = {"_id": "6555d6e5f1e4f1e4f1e4f1e4", "username": "tester"}


@asynccontextmanager
async def no_lifespan(_app):
    yield


@pytest.fixture(scope="session")
def test_app():
    # Désactive le lifespan réel (pas de connexions réelles DB/Qdrant)
    app.router.lifespan_context = no_lifespan

    # Objets fake attachés à l'app (pour les deps via request.app)
    app.mongodb_client = FakeMongoConnector()
    app.qdrant_client = FakeQdrantConnector()

    # Overrides de dépendances sécurité/DB/providers
    app.dependency_overrides[_ensure_valid_api_key_or_token] = lambda: True
    app.dependency_overrides[_get_current_user_with_api_key_or_token] = (
        lambda: TEST_USER
    )
    app.dependency_overrides[_ensure_valid_api_key_or_token_pkg] = lambda: True
    app.dependency_overrides[_get_current_user_with_api_key_or_token_pkg] = (
        lambda: TEST_USER
    )
    app.dependency_overrides[_get_mongo_client_dep] = lambda: app.mongodb_client
    app.dependency_overrides[_get_qdrant_client_dep] = lambda: app.qdrant_client

    # Overrides de classes (TextGeneration / Embeddings)
    def _get_embeddings_override():
        return Embeddings()

    def _get_text_generation_override():
        return TextGeneration()

    app.dependency_overrides[_get_embeddings_dep] = _get_embeddings_override
    app.dependency_overrides[_get_text_generation_dep] = _get_text_generation_override

    return app


@pytest.fixture()
def client(test_app):
    return TestClient(test_app)
