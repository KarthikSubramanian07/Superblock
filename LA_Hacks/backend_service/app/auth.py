import json
import os
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from urllib.request import urlopen

from app.settings import get_settings

settings = get_settings()
AUTH0_DOMAIN = settings.auth0_domain
AUTH0_AUDIENCE = settings.auth0_audience
ALGORITHMS = ["RS256"]

class Auth0Error(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

token_auth_scheme = HTTPBearer()

def get_auth0_user(token: HTTPAuthorizationCredentials = Depends(token_auth_scheme)):
    """Validates the Auth0 JWT token."""
    token = token.credentials
    try:
        jsonurl = urlopen(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=ALGORITHMS,
                    audience=AUTH0_AUDIENCE,
                    issuer=f"https://{AUTH0_DOMAIN}/"
                )
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is expired")
            except jwt.JWTClaimsError:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect claims, please check the audience and issuer")
            except Exception:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to parse authentication token")

            return payload
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to find appropriate key")
