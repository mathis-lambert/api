from datetime import timedelta

from api.v1.security import APIAuth, AuthError, oauth2_scheme
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status

from .auth_models import (
    GetTokenResponse,
    RegisterRequestBody,
    RegisterResponse,
    VerifyResponse,
)

router = APIRouter()


def get_auth(request: Request):
    auth_instance = APIAuth()
    auth_instance.set_mongo_client(request.app.mongodb_client)
    return auth_instance


@router.post(
    "/token",
    response_model=GetTokenResponse,
    summary="Obtenir un token d'accès",
    tags=["auth"],
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
            username, password, timedelta(minutes=expires_in)
        )
        return token_data
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/register",
    response_model=RegisterResponse,
    summary="Enregistrer un nouvel utilisateur",
    tags=["auth"],
)
async def register(
    auth_request: RegisterRequestBody, auth: APIAuth = Depends(get_auth)
):
    """Enregistre un nouvel utilisateur dans la base en mémoire."""
    try:
        new_user = await auth.register(
            auth_request.username, auth_request.password, auth_request.email
        )
        return {"msg": "Utilisateur enregistré avec succès", "user": new_user}
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/verify",
    response_model=VerifyResponse,
    summary="Vérifier le token d'accès",
    tags=["auth"],
)
async def verify(
    token: str = Depends(oauth2_scheme), auth: APIAuth = Depends(get_auth)
):
    """Vérifie la validité d'un token JWT et retourne l'utilisateur associé."""
    try:
        user = await auth.verify_token(token)
        return {"msg": "Token valide", "user": user}
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
