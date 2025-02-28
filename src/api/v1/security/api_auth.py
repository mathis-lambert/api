import hashlib
import hmac
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security.api_key import APIKeyHeader
from jwt.exceptions import PyJWTError

from api.utils import CustomLogger

from .oauth2_scheme import oauth2_scheme

logger = CustomLogger.get_logger(__name__)

load_dotenv()


class AuthError(Exception):
    """Exception personnalisée pour les erreurs d'authentification."""

    pass


class TooManyAPIKeysError(Exception):
    """Exception personnalisée pour le dépassement du nombre maximum de clés API."""

    pass


class APIKeyNotFoundError(Exception):
    """Exception personnalisée pour les clés API introuvables."""

    pass


class APIAuth:
    SECRET_KEY = os.getenv("SECRET_KEY")  # clé secret pour signer le token
    ALGORITHM = "HS256"  # algorithme de signature

    def __init__(self):
        self.mongo_client = None

    def set_mongo_client(self, mongo_client):
        self.mongo_client = mongo_client

        if mongo_client is None:
            raise ValueError("MongoDB client is required")

    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Retourne l'utilisateur correspondant ou None."""
        user = await self.mongo_client.find_one("users", {"username": username})
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retourne l'utilisateur correspondant à l'ID ou None."""
        user = await self.mongo_client.find_one("users", {"_id": user_id})
        return user

    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authentifie l'utilisateur en vérifiant son mot de passe."""
        user = await self.get_user(username)
        if not user:
            raise AuthError("Utilisateur introuvable")
        if not self.verify_password(password, user["hashed_password"]):
            raise AuthError("Mot de passe incorrect")
        return user

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] | None = None
    ) -> str:
        """Crée un token JWT contenant les données transmises,
        avec une expiration définie.
        """
        to_encode = data.copy()
        # If None, token expires in 30 minutes
        expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=30))
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def generate_token(
        self, username: str, password: str, expires: timedelta
    ) -> Dict[str, Any]:
        """Authentifie l'utilisateur et renvoie un dictionnaire contenant
        le token d'accès et le type de token.
        """
        user = await self.authenticate_user(username, password)
        token = self.create_access_token(
            data={"sub": user["username"]}, expires_delta=expires
        )
        return {"access_token": token, "token_type": "bearer"}

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Décode et vérifie le token JWT. Retourne l'utilisateur associé
        ou lève une AuthError en cas de problème.
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            username: Optional[str] = payload.get("sub")
            if username is None:
                raise AuthError("Token invalide : sujet manquant")
        except PyJWTError:
            raise AuthError("Token invalide ou expiré") from None
        user = await self.get_user(username)
        if user is None:
            raise AuthError("Utilisateur introuvable")
        return self.mongo_client.serialize(user)

    async def register(
        self, username: str, password: str, email: str
    ) -> Dict[str, Any]:
        """Crée un nouvel utilisateur dans la base en mémoire."""
        user = await self.get_user(username)
        if user:
            raise AuthError("L'utilisateur existe déjà")

        new_user = {
            "username": username,
            "email": email,
            "admin": False,
            "hashed_password": self.hash_password(password),
            "disabled": False,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        success = await self.mongo_client.insert_one("users", new_user)
        if not success:
            raise AuthError("Erreur lors de l'insertion de l'utilisateur")

        return self.mongo_client.serialize(new_user)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash le mot de passe en utilisant pbkdf2_hmac.
        On stocke le sel et le hash sous la forme 'sel$hash'.
        """
        salt = os.urandom(16)
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, 100_000
        )
        return salt.hex() + "$" + hash_bytes.hex()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Vérifie le mot de passe en recalculant le hash avec le sel stocké."""
        try:
            salt_hex, hash_hex = hashed.split("$")
        except ValueError:
            return False
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        new_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, 100_000
        )
        return hmac.compare_digest(new_hash, expected_hash)

    async def generate_api_key(
        self, username: str, expires_in: Optional[int] = None
    ) -> Dict[str, Any]:
        """Génère une clé API pour un utilisateur authentifié."""
        user = await self.get_user(username)
        if not user:
            raise AuthError("Utilisateur introuvable")

        if len(await self.list_api_keys(str(user["_id"]))) >= 10:
            raise TooManyAPIKeysError("Nombre maximum de clés API atteint")

        # Générer une clé API unique
        api_key = str(uuid.uuid4())

        # Calculer la date d'expiration si spécifiée
        expires_at = None
        if expires_in is not None:
            expires_at = datetime.now(UTC) + timedelta(minutes=expires_in)

        # Stocker la clé API dans la base de données
        api_key_data = {
            "api_key": api_key,
            "user_id": user["_id"],
            "created_at": datetime.now(UTC),
            "expires_at": expires_at,
        }

        api_key_id = await self.mongo_client.insert_one("api_keys", api_key_data)

        if not api_key_id:
            raise HTTPException(
                status_code=500, detail="Erreur lors de la génération de la clé API"
            )

        return {
            "api_key": api_key,
            "api_key_id": str(api_key_id),
            "expires_at": expires_at,
        }

    async def verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """Vérifie la validité d'une clé API et retourne l'utilisateur associé."""
        api_key_data = await self.mongo_client.find_one(
            "api_keys", {"api_key": api_key}
        )

        if not api_key_data:
            raise AuthError("Clé API invalide")

        if (
            api_key_data["expires_at"]
            and datetime.now(UTC) > api_key_data["expires_at"]
        ):
            self.mongo_client.delete_one("api_keys", {"api_key": api_key})
            raise AuthError("Clé API expirée")

        user = await self.get_user_by_id(api_key_data["user_id"])
        if not user:
            raise AuthError("Utilisateur introuvable")

        return self.mongo_client.serialize(user)

    async def list_api_keys(self, user_id: str) -> list[dict[str, Any]]:
        """Liste toutes les clés API d'un utilisateur."""
        api_keys = await self.mongo_client.find_many(
            "api_keys", {"user_id": ObjectId(user_id)}
        )

        # Convertir les ObjectId en chaînes de caractères
        for api_key in api_keys:
            api_key["_id"] = str(api_key["_id"])  # Convertir ObjectId en chaîne
            api_key["user_id"] = str(api_key["user_id"])  # Convertir ObjectId en chaîne
            if api_key["expires_at"]:
                api_key["expires_at"] = api_key["expires_at"].isoformat()
        return api_keys

    async def delete_api_key(self, user_id: str, api_key_id: str) -> None:
        """Supprime une clé API d'un utilisateur."""
        api_key = await self.mongo_client.find_one(
            "api_keys", {"_id": ObjectId(api_key_id), "user_id": ObjectId(user_id)}
        )
        if not api_key:
            raise APIKeyNotFoundError("Clé API introuvable")

        await self.mongo_client.delete_one("api_keys", {"_id": ObjectId(api_key_id)})

    async def get_user_by_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Retourne l'utilisateur correspondant à la clé API ou None."""
        api_key_data = await self.mongo_client.find_one(
            "api_keys", {"api_key": api_key}
        )
        if api_key_data:
            return await self.get_user_by_id(api_key_data["user_id"])
        return None


def get_auth(request: Request):
    auth_instance = APIAuth()
    auth_instance.set_mongo_client(request.app.mongodb_client)
    return auth_instance


async def get_current_user_with_api_key(
    api_key: str = Security(APIKeyHeader(name="X-ML-API-Key", auto_error=False)),
    auth: APIAuth = Depends(get_auth),
):
    """Dépendance qui vérifie le token via l'instance APIAuth.
    En cas d'erreur, une HTTPException 401 est levée.
    """
    try:
        if api_key:
            user = await auth.verify_api_key(api_key)
        else:
            raise HTTPException(status_code=401, detail="Clé API manquante")

    except Exception as e:
        logger.error("Erreur lors de la vérification du token: %s", e)
        raise HTTPException(status_code=401, detail="Token invalide ou expiré") from e
    return user


async def get_current_user_with_token(
    token: str = Depends(oauth2_scheme), auth: APIAuth = Depends(get_auth)
):
    """Dépendance qui vérifie le token via l'instance APIAuth.
    En cas d'erreur, une HTTPException 401 est levée.
    """
    try:
        user = await auth.verify_token(token)
    except Exception as e:
        logger.error("Erreur lors de la vérification du token: %s", e)
        raise HTTPException(status_code=401, detail="Token invalide ou expiré") from e
    return user


async def get_current_user_with_api_key_or_token(
    api_key: str = Security(APIKeyHeader(name="X-ML-API-Key", auto_error=False)),
    token: str = Depends(oauth2_scheme),
    auth: APIAuth = Depends(get_auth),
):
    """Dépendance qui vérifie le token via l'instance APIAuth.
    En cas d'erreur, une HTTPException 401 est levée.
    """
    try:
        if api_key:
            user = await auth.verify_api_key(api_key)
        elif token:
            user = await auth.verify_token(token)
        else:
            raise HTTPException(status_code=401, detail="Token ou clé API manquant")
    except Exception as e:
        logger.error("Erreur lors de la vérification du token: %s", e)
        raise HTTPException(
            status_code=401, detail="Token ou clé API invalide ou expiré"
        ) from e
    return user


async def ensure_valid_token(
    token: str = Depends(oauth2_scheme), auth: APIAuth = Depends(get_auth)
):
    """Dépendance qui vérifie le token via l'instance APIAuth.
    En cas d'erreur, une HTTPException 401 est levée.
    """
    try:
        await auth.verify_token(token)
    except Exception as e:
        logger.error("Erreur lors de la vérification du token: %s", e)
        raise HTTPException(status_code=401, detail="Token invalide ou expiré") from e
    return True


async def ensure_valid_api_key(
    api_key: str = Security(APIKeyHeader(name="X-ML-API-Key", auto_error=True)),
    auth: APIAuth = Depends(get_auth),
):
    """Dépendance qui vérifie la clé API via l'instance APIAuth.
    En cas d'erreur, une HTTPException 401 est levée.
    """
    try:
        await auth.verify_api_key(api_key)
    except AuthError as e:
        logger.error("Erreur lors de la vérification de la clé API: %s", e)
        raise HTTPException(
            status_code=401,
            detail="Clé API invalide ou expirée",
            headers={"WWW-Authenticate": "API-Key"},
        ) from e
    return True


async def ensure_valid_api_key_or_token(
    api_key: str = Security(APIKeyHeader(name="X-ML-API-Key", auto_error=False)),
    token: str = Depends(oauth2_scheme),
    auth: APIAuth = Depends(get_auth),
):
    """Dépendance qui vérifie la clé API ou le token via l'instance APIAuth.
    En cas d'erreur, une HTTPException 401 est levée.
    """
    try:
        if api_key:
            await auth.verify_api_key(api_key)
        elif token:
            await auth.verify_token(token)
        else:
            raise HTTPException(status_code=401, detail="Token ou clé API manquant")
    except Exception as e:
        logger.error("Erreur lors de la vérification du token ou de la clé API: %s", e)
        raise HTTPException(
            status_code=401, detail="Token ou clé API invalide ou expiré"
        ) from e
    return True
