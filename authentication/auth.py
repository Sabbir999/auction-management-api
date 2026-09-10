from django.contrib.auth import get_user_model
from firebase_admin import auth
from ninja.security import HttpBearer

from authentication.firebase import firebase_app


User = get_user_model()


def verify_firebase_token(token):
    try:
        return auth.verify_id_token(
            token,
            app=firebase_app,
            check_revoked=True,
        )
    except (
        auth.InvalidIdTokenError,
        auth.ExpiredIdTokenError,
        auth.RevokedIdTokenError,
        auth.UserDisabledError,
    ):
        return None


class FirebaseTokenAuth(HttpBearer):
    """
    Firebase authentication only.

    Used during registration because the Django
    user may not exist yet.
    """

    def authenticate(self, request, token):
        return verify_firebase_token(token)


class FirebaseAuth(HttpBearer):
    """
    Firebase authentication + Django user lookup.

    Used for normal authenticated API endpoints.
    """

    def authenticate(self, request, token):
        decoded_token = verify_firebase_token(token)

        if not decoded_token:
            return None

        firebase_uid = decoded_token.get("uid")

        if not firebase_uid:
            return None

        user = User.objects.filter(firebase_uid=firebase_uid, is_active=True).first()

        if not user:
            return None

        request.user = user
        request.firebase_claims = decoded_token

        return user


firebase_token_auth = FirebaseTokenAuth()
firebase_auth = FirebaseAuth()