from bson import ObjectId
from fastapi import Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from api.v1.security import get_current_user

from .get_databases import get_mongo_client


async def check_collection_ownership(
    collection_name: str,
    user: dict = Depends(get_current_user),
    mongo_client: AsyncIOMotorClient = Depends(get_mongo_client),
):
    """Get user's collection from MongoDB."""
    users_collections = await mongo_client.find_many(
        "vector_db_collections",
        {"user_id": ObjectId(user["_id"]), "name": collection_name},
    )

    if not users_collections:
        raise HTTPException(status_code=403, detail="No collection found for this user")

    return True
