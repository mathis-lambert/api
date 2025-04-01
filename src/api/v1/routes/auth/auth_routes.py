from datetime import timedelta
from typing import List

from api.v1.security import (
    APIAuth,
    APIKeyNotFoundError,
    AuthError,
    TooManyAPIKeysError,
    ensure_valid_api_key_or_token,
    ensure_valid_token,
    get_auth,
    get_current_user_with_api_key_or_token,
    get_current_user_with_token,
    oauth2_scheme,
)
from fastapi import APIRouter, Depends, Form, HTTPException, status

from .auth_models import (
    ApiKeyEntry,
    DeleteApiKeyResponse,
    GetApiKeyRequestBody,
    GetApiKeyResponse,
    GetTokenResponse,
    RegisterRequestBody,
    RegisterResponse,
    VerifyResponse,
)

router = APIRouter()


@router.post(
    "/token",
    response_model=GetTokenResponse,
    summary="Obtenir un token d'accès",
)
async def login(
    username: str = Form(...),
    password: str = Form(...),
    expires_in: int = Form(30),  # Par défaut, le token expire dans 30 minutes
    auth: APIAuth = Depends(get_auth),
):
    """Authentifie l'utilisateur et retourne un token JWT."""
    try:
        token_data = await auth.generate_token(
            username,
            password,
            timedelta(minutes=expires_in) if expires_in > 0 else None,
        )
        return token_data
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


@router.post(
    "/api-key",
    response_model=GetApiKeyResponse,
    summary="Générer une clé API",
    dependencies=[Depends(ensure_valid_token)],
)
async def generate_api_key(
    body: GetApiKeyRequestBody,
    auth: APIAuth = Depends(get_auth),
    user: dict = Depends(get_current_user_with_token),
):
    """Génère une clé API pour un utilisateur authentifié."""
    try:
        api_key_data = await auth.generate_api_key(
            user["username"],
            expires_in=body.expires_in,
        )
        return api_key_data
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except TooManyAPIKeysError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


@router.get(
    "/api-keys",
    response_model=List[ApiKeyEntry],
    summary="Lister toutes les clés API de l'utilisateur",
    dependencies=[Depends(ensure_valid_api_key_or_token)],
)
async def list_api_keys(
    auth: APIAuth = Depends(get_auth),
    user: dict = Depends(get_current_user_with_api_key_or_token),
):
    """Liste toutes les clés API de l'utilisateur authentifié."""
    try:
        api_keys = await auth.list_api_keys(str(user["_id"]))
        return api_keys
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


@router.delete(
    "/api-key/{api_key_id}",
    response_model=DeleteApiKeyResponse,
    summary="Supprimer une clé API",
    dependencies=[Depends(ensure_valid_api_key_or_token)],
)
async def delete_api_key(
    api_key_id: str,
    auth: APIAuth = Depends(get_auth),
    user: dict = Depends(get_current_user_with_api_key_or_token),
):
    """Supprime une clé API de l'utilisateur authentifié."""
    try:
        await auth.delete_api_key(str(user["_id"]), api_key_id)
        return {"msg": "Clé API supprimée avec succès", "success": True}
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except APIKeyNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


# @router.post(
#     "/register",
#     response_model=RegisterResponse,
#     summary="Enregistrer un nouvel utilisateur",
# )
# async def register(
#     auth_request: RegisterRequestBody, auth: APIAuth = Depends(get_auth)
# ):
#     """Enregistre un nouvel utilisateur dans la base en mémoire."""
#     try:
#         new_user = await auth.register(
#             auth_request.username, auth_request.password, auth_request.email
#         )
#         return {"msg": "Utilisateur enregistré avec succès", "user": new_user}
#     except AuthError as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
#         ) from e


@router.get(
    "/verify",
    response_model=VerifyResponse,
    summary="Vérifier le token d'accès",
)
async def verify(
    token: str = Depends(oauth2_scheme), auth: APIAuth = Depends(get_auth)
):
    """Vérifie la validité d'un token JWT et retourne l'utilisateur associé."""
    try:
        user = await auth.verify_token(token)
        return {"msg": "Token valide", "user": user}
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e
