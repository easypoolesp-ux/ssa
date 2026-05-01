# =============================================================================
# SSA Alumni — Firebase JWT Authentication
# Responsibility: Verify Firebase ID tokens from the Authorization header.
#                 One class, one job (SOLID: SRP).
# =============================================================================

from __future__ import annotations

import logging
import os

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Initialise the Firebase Admin SDK once at module load time.
# Uses Application Default Credentials (ADC) on Cloud Run automatically.
# ---------------------------------------------------------------------------
if not firebase_admin._apps:
    _cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(_cred)


class FirebaseUser:
    """
    Lightweight user object attached to request.user after token verification.

    Intentionally does NOT touch the Django auth User table — auth is
    delegated entirely to Firebase.  Profile data lives in AlumniProfile.
    """

    def __init__(self, uid: str, email: str | None, token: dict) -> None:
        self.uid = uid
        self.email = email
        self.token = token
        self.is_authenticated = True
        self.is_anonymous = False

    def __str__(self) -> str:
        return self.email or self.uid


class FirebaseAuthentication(BaseAuthentication):
    """
    DRF authentication backend that validates Firebase ID tokens.

    Flow:
        1. Extract `Bearer <token>` from the Authorization header.
        2. Verify the token with Firebase Admin SDK.
        3. Return (FirebaseUser, token_payload) on success.
        4. Raise AuthenticationFailed on any token problem.
        5. Return None if no Authorization header present (allows
           unauthenticated read access per permission class).

    Dev escape hatch:
        Set SKIP_FIREBASE_AUTH=true to bypass verification in local dev.
        A synthetic FirebaseUser(uid='dev-user') is returned instead.
    """

    keyword = "Bearer"

    def authenticate(self, request: Request):
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header:
            return None  # No credentials supplied → anonymous

        if not header.startswith(f"{self.keyword} "):
            return None  # Not a Bearer token — let other backends try

        id_token = header[len(self.keyword) + 1:].strip()

        # ── Dev bypass ──────────────────────────────────────────────────────
        if os.environ.get("SKIP_FIREBASE_AUTH", "False").lower() == "true":
            logger.warning("SKIP_FIREBASE_AUTH is enabled — bypassing token verification.")
            user = FirebaseUser(uid="dev-user", email="dev@local", token={})
            return (user, None)

        # ── Verify token ─────────────────────────────────────────────────────
        try:
            decoded = firebase_auth.verify_id_token(id_token)
        except firebase_auth.ExpiredIdTokenError:
            raise AuthenticationFailed("Firebase token has expired.")
        except firebase_auth.RevokedIdTokenError:
            raise AuthenticationFailed("Firebase token has been revoked.")
        except firebase_auth.InvalidIdTokenError as exc:
            raise AuthenticationFailed(f"Invalid Firebase token: {exc}")
        except Exception as exc:
            logger.error("Firebase token verification error: %s", exc)
            raise AuthenticationFailed("Token verification failed.")

        user = FirebaseUser(
            uid=decoded["uid"],
            email=decoded.get("email"),
            token=decoded,
        )
        return (user, decoded)

    def authenticate_header(self, request: Request) -> str:
        return self.keyword
