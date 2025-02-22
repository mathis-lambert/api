import os
from typing import List

from dotenv import load_dotenv
from qdrant_client import AsyncQdrantClient, models

from api.utils import CustomLogger

logger = CustomLogger.get_logger(__name__)

load_dotenv()


class QdrantConnector:
    def __init__(self):
        # Récupérer les variables d'environnement
        self.api_key = os.getenv("QDRANT_API_KEY")
        self.url = os.getenv("QDRANT_URL")

        if not self.api_key or not self.url:
            raise ValueError(
                "Les variables d'environnement QDRANT_API_KEY et QDRANT_URL doivent être définies."
            )

        # Initialiser le client Qdrant asynchrone
        self.client = AsyncQdrantClient(url=self.url, api_key=self.api_key)

    async def check_connection(self):
        """Vérifie la connexion à Qdrant de manière asynchrone.
        :return: True si la connexion est réussie, False sinon.
        """
        try:
            await self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Erreur de connexion à Qdrant: {e}")
            return False

    def get_client(self):
        """Récupère le client Qdrant.
        :return: Instance du client Qdrant.
        """
        return self.client

    async def list_collections(self):
        """Liste toutes les collections existantes dans Qdrant de manière asynchrone.
        :return: Dictionnaire contenant les collections.
        """
        collections = await self.client.get_collections()
        return collections

    async def get_collection(self, collection_name):
        """Récupère les informations d'une collection spécifique dans Qdrant de manière asynchrone.

        :param collection_name: Nom de la collection.
        :return: Dictionnaire contenant les informations de la collection.
        """
        try:
            return await self.client.get_collection(collection_name=collection_name)
        except Exception as e:
            logger.error(
                f"Erreur lors de la récupération de la collection '{collection_name}': {e}"
            )
            return None

    async def upsert(self, collection_name, points):
        """Insère ou met à jour des points dans une collection Qdrant de manière asynchrone.

        :param collection_name: Nom de la collection.
        :param points: Liste de points à insérer ou mettre à jour.
        """
        await self.client.upsert(collection_name=collection_name, points=points)

    async def batch_upsert(self, collection_name, indexes, vectors, payloads=None):
        """Insère ou met à jour des points dans une collection Qdrant de manière asynchrone.

        :param collection_name: Nom de la collection.
        :param indexes: Liste d'index pour les points.
        :param vectors: Liste de vecteurs à insérer ou mettre à jour.
        :param payloads: Liste optionnelle de payloads associés aux vecteurs.
        """
        if payloads is None:
            payloads = [{}] * len(vectors)

        points = models.Batch(
            ids=indexes,
            vectors=vectors,
            payloads=payloads,
        )

        await self.client.upsert(collection_name=collection_name, points=points)

    async def create_collection(
        self, collection_name, vector_size=1024, distance="Cosine"
    ):
        """Crée une nouvelle collection dans Qdrant de manière asynchrone.

        :param collection_name: Nom de la collection.
        :param vector_size: Taille des vecteurs de la collection (par défaut 1024).
        :param distance: Métrique de distance (par défaut "Cosine", peut être "Euclidean", etc.).
        """
        if distance not in ["Cosine", "Euclidean"]:
            raise ValueError("La distance doit être 'Cosine' ou 'Euclidean'.")

        if await self.client.create_collection(
            vectors_config=models.VectorParams(size=vector_size, distance=distance),
            collection_name=collection_name,
        ):
            logger.info(f"Collection '{collection_name}' créée avec succès.")
            return True
        else:
            logger.error(f"Échec de la création de la collection '{collection_name}'.")
            return False

    async def search_in_collection(
        self, collection_name, query_vector, limit=5
    ) -> List[dict]:
        """Recherche des vecteurs similaires dans une collection Qdrant de manière asynchrone.

        :param collection_name: Nom de la collection.
        :param query_vector: Vecteur de requête.
        :param limit: Nombre maximum de résultats à retourner.
        :return: Résultat de la recherche.
        """
        if not await self.client.get_collection(collection_name):
            raise ValueError(f"La collection '{collection_name}' n'existe pas.")

        result = await self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            with_vectors=True,
            with_payload=True,
            limit=limit,
        )
        # sort by score
        result.points.sort(key=lambda x: x.score, reverse=True)

        # get payload
        return [
            {"payload": point.payload, "score": point.score} for point in result.points
        ]

    async def delete_collection(self, collection_name):
        """Supprime une collection dans Qdrant de manière asynchrone.

        :param collection_name: Nom de la collection à supprimer.
        """
        await self.client.delete_collection(collection_name=collection_name)

    async def insert_vectors(self, collection_name, vectors, payloads=None):
        """Insère des vecteurs dans une collection Qdrant de manière asynchrone.

        :param collection_name: Nom de la collection.
        :param vectors: Liste de vecteurs à insérer.
        :param payloads: Liste optionnelle de payloads associés aux vecteurs.
        """
        if payloads is None:
            payloads = [{}] * len(vectors)

        points = [
            models.PointStruct(id=idx, vector=vector, payload=payload)
            for idx, (vector, payload) in enumerate(zip(vectors, payloads))
        ]

        await self.client.upsert(collection_name=collection_name, points=points)

    async def retrieve_vectors(self, collection_name, query_vector, top=5):
        """Récupère les vecteurs les plus similaires à un vecteur de requête de manière asynchrone.

        Cette méthode utilise `query_points` pour réaliser la recherche des vecteurs.

        :param collection_name: Nom de la collection.
        :param query_vector: Vecteur de requête.
        :param top: Nombre de vecteurs similaires à récupérer.
        :return: Résultat de la requête contenant les vecteurs similaires.
        """
        result = await self.client.query_points(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top,  # Remplace l'ancien paramètre 'top'
            with_payload=True,  # Inclut les payloads dans le résultat
            with_vectors=False,  # Ne récupère pas les vecteurs complets
        )
        return result

    async def close(self):
        """Ferme la connexion avec Qdrant de manière asynchrone."""
        await self.client.close()
