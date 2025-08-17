from api.classes import Embeddings, Models, TextGeneration


def get_embeddings() -> Embeddings:
    return Embeddings()


def get_text_generation() -> TextGeneration:
    return TextGeneration()


def get_models() -> Models:
    return Models()
