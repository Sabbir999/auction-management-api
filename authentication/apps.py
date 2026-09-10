from django.apps import AppConfig
from django.db.models.signals import post_migrate


def sync_application_roles(sender, **kwargs):
    from authentication.services.role_service import RoleService

    RoleService.sync_roles()


class AuthenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "authentication"

    def ready(self):
        post_migrate.connect(
            sync_application_roles,
            dispatch_uid="authentication.sync_application_roles",
        )