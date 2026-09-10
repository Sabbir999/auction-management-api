from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from ninja import Router

from .auth import firebase_auth, firebase_token_auth
from .schemas import (
    UserResponse, UserUpdate,
    AccessRequestCreate, AccessRequestResponse, AccessRoleResponse
)
from .roles import get_requestable_roles
from .services.access_request_service import AccessRequestService


router = Router(tags=["Authentication"], auth=firebase_auth)

User = get_user_model()


@router.get(
    path="/roles",
    summary="Get available roles",
    description="Returns requestable application roles and the user's current access.",
    response=list[AccessRoleResponse],
)
def get_roles(request):
    user_group_names = set(
        request.auth.groups.values_list("name", flat=True)
    )

    return [
        {
            "key": role.key,
            "name": role.name,
            "description": role.description,
            "requestable": role.requestable,
            "has_role": role.name in user_group_names,
        }
        for role in get_requestable_roles()
    ]

@router.post(
    path="/access-requests",
    summary="Request access",
    description="Requests a Draftboard application role.",
    response={
        201: AccessRequestResponse,
        400: dict,
    },
)
def create_access_request(request, payload: AccessRequestCreate):
    try:
        access_request = AccessRequestService.create_request(
            user=request.auth,
            role_key=payload.requested_role,
            reason=payload.reason,
        )
    except ValueError as exc:
        return 400, {
            "detail": str(exc),
        }

    return 201, access_request


@router.post(
    path="/register",
    summary="Register a user",
    description="Creates a Draftboard user from the authenticated Firebase account.",
    url_name="register-user",
    auth=firebase_token_auth,
    response={
        200: UserResponse,
        201: UserResponse,
        400: dict,
        409: dict,
    },
)
def register_user(request):
    firebase_uid = request.auth["uid"]
    email = request.auth.get("email")
    email_verified = request.auth.get(
        "email_verified",
        False,
    )

    if not email:
        return 400, {
            "detail": "Firebase account does not contain an email address."
        }

    email = email.strip().lower()

    existing_user = User.objects.filter(
        firebase_uid=firebase_uid,
    ).first()

    if existing_user:
        return 200, existing_user

    if User.objects.filter(
        email__iexact=email,
    ).exists():
        return 409, {
            "detail": "A user with this email already exists."
        }

    try:
        with transaction.atomic():
            user = User.objects.create_firebase_user(
                email=email,
                firebase_uid=firebase_uid,
                email_verified=email_verified,
            )

    except IntegrityError:
        existing_user = User.objects.filter(
            firebase_uid=firebase_uid,
        ).first()

        if existing_user:
            return 200, existing_user

        return 409, {
            "detail": "Unable to create user because the account already exists."
        }

    return 201, user


@router.get(
    path="/me",
    summary="Get current user",
    description="Returns the authenticated Draftboard user.",
    url_name="get-current-user",
    response={
        200: UserResponse,
    },
)
def get_current_user(request):
    return 200, request.auth


@router.patch(
    path="/me",
    summary="Update current user",
    description="Updates the authenticated user's own profile.",
    url_name="update-current-user",
    response={
        200: UserResponse,
    },
)
def update_current_user(request, payload: UserUpdate):
    user = request.auth

    update_data = payload.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        setattr(
            user,
            field,
            value,
        )

    if update_data:
        user.save(
            update_fields=[
                *update_data.keys(),
                "updated_at",
            ]
        )

    return 200, user


@router.delete(
    path="/me",
    summary="Delete current user",
    description="Deletes the authenticated user's Draftboard profile.",
    url_name="delete-current-user",
    response={
        204: None,
    },
)
def delete_current_user(request):
    user = request.auth

    user.delete()

    return 204, None