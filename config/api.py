import sentry_sdk
from django.contrib.admin.views.decorators import staff_member_required
from ninja import NinjaAPI
from ninja.errors import ValidationError

from authentication.auth import FirebaseAuth
from authentication.api import router as authentication_router
from auctions.api import router as auction_router
from players.api import router as player_router


api = NinjaAPI(
    title="Draftboard API",
    version="1.0.0",
    description="Backend API for Draftboard auction and draft management.",
    docs_decorator=staff_member_required,
    auth=FirebaseAuth(),
)


def validation_exception_handler(request, exc):
    sentry_sdk.capture_exception(exc)

    sentry_sdk.capture_message(
        f"Request body: {request.body.decode('utf-8', errors='ignore')}"
    )

    return api.create_response(
        request,
        {"detail": exc.errors},
        status=422,
    )


api.add_exception_handler(
    ValidationError,
    validation_exception_handler,
)


api.add_router("/auth/", authentication_router)
api.add_router("/auctions/", auction_router)
api.add_router("/players/", player_router)