import os
from collections.abc import Callable
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidIssuerError,
    InvalidTokenError,
)


KEYCLOAK_ISSUER = os.getenv(
    "KEYCLOAK_ISSUER",
    "https://auth.local/realms/devops-lvlup",
)

KEYCLOAK_JWKS_URL = os.getenv(
    "KEYCLOAK_JWKS_URL",
    (
        "http://keycloak-keycloakx-http.keycloak.svc.cluster.local"
        "/realms/devops-lvlup/protocol/openid-connect/certs"
    ),
)

KEYCLOAK_AUDIENCE = os.getenv(
    "KEYCLOAK_AUDIENCE",
    "shopping-app",
)

bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Keycloak access token",
)

jwks_client = PyJWKClient(KEYCLOAK_JWKS_URL)


def unauthorized(detail: str = "Authentication required") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=KEYCLOAK_ISSUER,
            audience=KEYCLOAK_AUDIENCE,
            options={
                "require": ["exp", "iat", "iss", "sub"],
            },
        )

    except ExpiredSignatureError as exc:
        raise unauthorized("Token has expired") from exc

    except InvalidIssuerError as exc:
        raise unauthorized("Invalid token issuer") from exc

    except InvalidTokenError as exc:
        raise unauthorized("Invalid access token") from exc

    except Exception as exc:
        raise unauthorized("Unable to validate access token") from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> dict[str, Any]:
    if credentials is None:
        raise unauthorized()

    if credentials.scheme.lower() != "bearer":
        raise unauthorized("Bearer token required")

    claims = decode_access_token(credentials.credentials)

    realm_access = claims.get("realm_access", {})
    roles = realm_access.get("roles", [])

    return {
        "sub": claims.get("sub"),
        "username": claims.get("preferred_username"),
        "roles": roles,
        "claims": claims,
    }


def require_roles(
    *allowed_roles: str,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def dependency(
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        user_roles = set(user.get("roles", []))
        required_roles = set(allowed_roles)

        if user_roles.isdisjoint(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Insufficient permissions",
                    "required_roles": sorted(required_roles),
                },
            )

        return user

    return dependency
