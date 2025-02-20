import hashlib
import hmac
import os
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request
from jwt.exceptions import PyJWTError

from lm_api.utils import CustomLogger
from .oauth2_scheme import oauth2_scheme

logger = CustomLogger.get_logger(__name__)

load_dotenv()


class AuthError(Exception):
    """Exception personnalisée pour les erreurs d'authentification."""
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

    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authentifie l'utilisateur en vérifiant son mot de passe."""
        user = await self.get_user(username)
        if not user:
            raise AuthError("Utilisateur introuvable")
        if not self.verify_password(password, user["hashed_password"]):
            raise AuthError("Mot de passe incorrect")
        return user

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crée un token JWT contenant les données transmises,
        avec une expiration définie.
        """
        to_encode = data.copy()
        expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=15))
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def generate_token(self, username: str, password: str, expires: timedelta) -> Dict[str, Any]:
        """
        Authentifie l'utilisateur et renvoie un dictionnaire contenant
        le token d'accès et le type de token.
        """
        user = await self.authenticate_user(username, password)
        token = self.create_access_token(data={"sub": user["username"]}, expires_delta=expires)
        return {"access_token": token, "token_type": "bearer"}

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Décode et vérifie le token JWT. Retourne l'utilisateur associé
        ou lève une AuthError en cas de problème.
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            username: Optional[str] = payload.get("sub")
            if username is None:
                raise AuthError("Token invalide : sujet manquant")
        except PyJWTError:
            raise AuthError("Token invalide ou expiré")
        user = await self.get_user(username)
        if user is None:
            raise AuthError("Utilisateur introuvable")
        return self.mongo_client.serialize(user)

    async def register(self, username: str, password: str, email: str) -> Dict[str, Any]:
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
        """
        Hash le mot de passe en utilisant pbkdf2_hmac.
        On stocke le sel et le hash sous la forme 'sel$hash'.
        """
        salt = os.urandom(16)
        hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return salt.hex() + "$" + hash_bytes.hex()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Vérifie le mot de passe en recalculant le hash avec le sel stocké.
        """
        try:
            salt_hex, hash_hex = hashed.split("$")
        except ValueError:
            return False
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        new_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(new_hash, expected_hash)


def get_auth(request: Request):
    auth_instance = APIAuth()
    auth_instance.set_mongo_client(request.app.mongodb_client)
    return auth_instance


async def get_current_user(token: str = Depends(oauth2_scheme), auth: APIAuth = Depends(get_auth)):
    """
    Dépendance qui vérifie le token via l'instance APIAuth.
    En cas d'erreur, une HTTPException 401 est levée.
    """
    try:
        user = await auth.verify_token(token)
    except Exception as e:
        logger.error("Erreur lors de la vérification du token: %s", e)
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    return user


async def ensure_valid_token(token: str = Depends(oauth2_scheme), auth: APIAuth = Depends(get_auth)):
    """
    Dépendance qui vérifie le token via l'instance APIAuth.
    En cas d'erreur, une HTTPException 401 est levée.
    """
    try:
        await auth.verify_token(token)
    except Exception as e:
        logger.error("Erreur lors de la vérification du token: %s", e)
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    return True
