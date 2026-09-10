import logging

from django.contrib.auth.models import Group, Permission
from django.db import transaction

from authentication.roles import (
    ROLE_DEFINITIONS,
    RoleDefinition,
    get_role,
)

logger = logging.getLogger(__name__)


class RoleService:
    @staticmethod
    def get_role(role_key: str) -> RoleDefinition:
        role = get_role(role_key)
        if not role:
            raise ValueError(f"Invalid role: {role_key}")
        return role

    @classmethod
    @transaction.atomic
    def sync_roles(cls) -> None:
        permission_names = {
            permission_name
            for role in ROLE_DEFINITIONS.values()
            for permission_name in role.permissions
        }

        app_labels = {
            permission_name.split(".", 1)[0]
            for permission_name in permission_names
        }

        codenames = {
            permission_name.split(".", 1)[1]
            for permission_name in permission_names
        }

        permissions = Permission.objects.select_related("content_type").filter(
            content_type__app_label__in=app_labels,
            codename__in=codenames,
        )

        permissions_by_name = {
            f"{permission.content_type.app_label}.{permission.codename}": permission
            for permission in permissions
        }

        for role in ROLE_DEFINITIONS.values():
            group, _ = Group.objects.get_or_create(name=role.name)

            role_permissions = [
                permissions_by_name[permission_name]
                for permission_name in role.permissions
                if permission_name in permissions_by_name
            ]

            group.permissions.set(role_permissions)

            missing_permissions = [
                permission_name
                for permission_name in role.permissions
                if permission_name not in permissions_by_name
            ]

            if missing_permissions:
                logger.warning(
                    "Role %s has missing permissions: %s",
                    role.key,
                    missing_permissions,
                )

    @classmethod
    def user_has_role(cls, user, role_key: str) -> bool:
        role = cls.get_role(role_key)
        return user.groups.filter(name=role.name).exists()

    @classmethod
    def assign_role(cls, user, role_key: str) -> None:
        role = cls.get_role(role_key)
        try:
            group = Group.objects.get(name=role.name)
        except Group.DoesNotExist:
            raise ValueError(f"Role '{role.name}' has not been synchronized.")

        user.groups.add(group)

    @classmethod
    def remove_role(cls, user, role_key: str) -> None:
        role = cls.get_role(role_key)
        group = Group.objects.filter(name=role.name).first()
        if group:
            user.groups.remove(group)