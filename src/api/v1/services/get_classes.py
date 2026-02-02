from api.classes import Embeddings, Models, OpenRouterProxy


def get_embeddings() -> Embeddings:
    return Embeddings()


def get_models() -> Models:
    return Models()


def get_openrouter_proxy() -> OpenRouterProxy:
    return OpenRouterProxy()
