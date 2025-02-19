# Utilise une image de base officielle Python
FROM python:3.13-slim

# Définit les variables d'environnement pour éviter le buffering de Python
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Définit le répertoire de travail dans le conteneur
WORKDIR /app

# Copie les fichiers de dépendances dans le conteneur
COPY pyproject.toml poetry.lock ./

# Installe Poetry
RUN pip install poetry

# Installe les dépendances du projet
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-root

# Copie le reste de l'application dans le conteneur
COPY . .

# Commande pour exécuter l'application avec Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Expose le port sur lequel l'application va tourner
EXPOSE 8000
