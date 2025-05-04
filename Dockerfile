# Utilise une image de base officielle Python
FROM python:3.13-slim

# Empêche Python de bufferer les logs et d'écrire les .pyc
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Répertoire de travail
WORKDIR /app

# Copie le fichier de dépendances et installe curl pour le HEALTHCHECK
COPY pyproject.toml ./
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copie le reste de l'application
COPY . .

# Installe les dépendances Python
RUN pip install --no-cache-dir .

# Déclare une commande HEALTHCHECK intégrée à l'image
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/v1/health || exit 1

# Expose le port de l'API
EXPOSE 8000

# Commande par défaut
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
