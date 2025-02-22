import asyncio
import signal
import sys

from api.databases import MongoDBConnector, QdrantConnector

from .logger import CustomLogger

logger = CustomLogger().get_logger(__name__)


def handle_sigint(signal, frame):
    logger.info("Interruption reçue. Arrêt du programme...")
    sys.exit(0)


signal.signal(signal.SIGINT, handle_sigint)


async def ensure_database_connection():
    mongodb_client = MongoDBConnector()
    qdrant_client = QdrantConnector()

    while not await mongodb_client.check_connection():
        logger.error("MongoDB connection failed. Retrying in 5 seconds...")
        await asyncio.sleep(5)

    logger.debug("MongoDB connection successful.")

    while not await qdrant_client.check_connection():
        logger.error("Qdrant connection failed. Retrying in 5 seconds...")
        await asyncio.sleep(5)

    logger.debug("Qdrant connection successful.")

    return mongodb_client, qdrant_client
