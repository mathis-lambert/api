import logging
import sys


class CustomLogger:
    """CustomLogger est une classe utilitaire qui fournit un logger configuré
    avec un formatage personnalisé. Ce logger affiche la date, le niveau de log,
    le nom du logger et le message, ce qui facilite la lecture et le débogage.
    """

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Retourne un logger avec le nom spécifié, configuré avec un format de log personnalisé.
        Si le logger possède déjà des handlers, il ne les ajoute pas à nouveau pour éviter les doublons.
        """
        logger = logging.getLogger(name)
        if not logger.handlers:  # Empêche l'ajout multiple de handlers
            logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                fmt="[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setLevel(logging.DEBUG)
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)
        return logger
