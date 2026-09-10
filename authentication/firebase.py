import os

import firebase_admin
from firebase_admin import credentials


def initialize_firebase():
    try:
        return firebase_admin.get_app()

    except ValueError:
        firebase_credentials = {
            "type": os.environ.get("FIREBASE_TYPE"),
            "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
            "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.environ.get("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
            "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
            "auth_uri": os.environ.get("FIREBASE_AUTH_URI"),
            "token_uri": os.environ.get("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.environ.get(
                "FIREBASE_AUTH_PROVIDER_X509_CERT_URL"
            ),
            "client_x509_cert_url": os.environ.get(
                "FIREBASE_CLIENT_X509_CERT_URL"
            ),
            "universe_domain": os.environ.get(
                "FIREBASE_UNIVERSE_DOMAIN",
                "googleapis.com",
            ),
        }

        credential = credentials.Certificate(firebase_credentials)

        return firebase_admin.initialize_app(credential)


firebase_app = initialize_firebase()