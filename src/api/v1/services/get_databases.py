from fastapi import Request


def get_mongo_client(request: Request):
    """Get MongoDB client from request."""
    return request.app.mongodb_client


def get_qdrant_client(request: Request):
    """Get Qdrant client from request."""
    return request.app.qdrant_client
