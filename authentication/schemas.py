from datetime import datetime
from typing import Optional
from authentication.roles import get_role

from ninja import Schema, Field


class AccessRoleResponse(Schema):
    key: str
    name: str
    description: str
    requestable: bool
    has_role: bool


class AccessRequestCreate(Schema):
    requested_role: str
    reason: str = Field(
        default="",
        max_length=1000,
    )


class AccessRequestResponse(Schema):
    id: int
    requested_role: str
    role_name: str
    reason: str
    status: str
    created_at: datetime
    reviewed_at: datetime | None = None

    @staticmethod
    def resolve_role_name(obj):
        role = get_role(obj.requested_role)

        return (
            role.name
            if role
            else obj.requested_role
        )


class UserResponse(Schema):
    id: int
    firebase_uid: Optional[str] = None
    email: str
    first_name: str
    last_name: str
    display_name: str
    email_verified: bool
    date_joined: datetime
    updated_at: datetime


class UserUpdate(Schema):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None


