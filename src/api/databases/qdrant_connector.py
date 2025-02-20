import os

from dotenv import load_dotenv
from qdrant_client import AsyncQdrantClient, models

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

    async def create_collection(self, collection_name, vector_size, distance="Cosine"):
        """Crée une nouvelle collection dans Qdrant de manière asynchrone.

        :param collection_name: Nom de la collection.
        :param vector_size: Taille des vecteurs de la collection.
        :param distance: Métrique de distance (par défaut "Cosine", peut être "Euclidean", etc.).
        """
        params = models.CollectionParams(
            vectors=models.VectorParams(size=vector_size, distance=distance)
        )
        await self.client.create_collection(
            collection_name=collection_name, collection_params=params
        )

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
