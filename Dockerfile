# Utilise une image de base officielle Python
FROM python:3.13-slim

# Définit les variables d'environnement pour éviter le buffering de Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Définit le répertoire de travail dans le conteneur
WORKDIR /app

# Copie le fichier de dépendances dans le conteneur
COPY pyproject.toml ./

# Copie le reste de l'application dans le conteneur
COPY . .

# Installe les dépendances du projet
RUN pip install --no-cache-dir .

# Commande pour exécuter l'application avec Uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Expose le port sur lequel l'application va tourner
EXPOSE 8000
