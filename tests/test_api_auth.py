import os
os.environ["SECRET_KEY"]="test"
from datetime import timedelta

import pytest

from api.v1.security.api_auth import APIAuth


class DummyMongo:
    def __init__(self):
        self.user = {"_id": "u", "username": "me", "hashed_password": ""}

    async def find_one(self, collection, query, projection=None):
        if collection == "users" and query.get("username") == "me":
            return self.user
        if collection == "users" and query.get("_id") == "u":
            return self.user
        return None

    async def insert_one(self, collection, doc):
        return True

    def serialize(self, doc):
        return doc


@pytest.mark.asyncio
async def test_password_hash_and_verify():
    auth = APIAuth()
    pw = "secret"
    hashed = auth.hash_password(pw)
    assert auth.verify_password(pw, hashed)


@pytest.mark.asyncio
async def test_token_roundtrip():
    os.environ["SECRET_KEY"] = "s"
    auth = APIAuth()
    auth.set_mongo_client(DummyMongo())
    token = auth.create_access_token({"sub": "me"}, timedelta(minutes=1))
    user = await auth.verify_token(token)
    assert user["username"] == "me"
