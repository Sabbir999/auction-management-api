from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

from authentication.models import AccessRequest, User
from authentication.roles import get_role
from authentication.services.access_request_service import AccessRequestService


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = [
        "id",
        "email",
        "display_name",
        "email_verified",
        "is_staff",
        "is_superuser",
        "is_active",
    ]

    list_filter = [
        "is_staff",
        "is_superuser",
        "is_active",
        "email_verified",
    ]

    search_fields = [
        "email",
        "display_name",
        "firebase_uid",
    ]

    ordering = [
        "email",
    ]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                )
            },
        ),
        (
            "Profile",
            {
                "fields": (
                    "display_name",
                    "firebase_uid",
                    "email_verified",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                    "is_active",
                ),
            },
        ),
    )

    readonly_fields = [
        "firebase_uid",
        "email_verified",
        "last_login",
        "date_joined",
    ]

    filter_horizontal = [
        "groups",
        "user_permissions",
    ]


@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "role_name",
        "status",
        "created_at",
        "reviewed_by",
        "reviewed_at",
    ]

    list_filter = [
        "status",
        "requested_role",
    ]

    search_fields = [
        "user__email",
        "reason",
    ]

    ordering = [
        "-created_at",
    ]

    readonly_fields = [
        "user",
        "requested_role",
        "reason",
        "status",
        "reviewed_by",
        "reviewed_at",
        "created_at",
        "updated_at",
    ]

    list_select_related = [
        "user",
        "reviewed_by",
    ]

    actions = [
        "approve_requests",
        "reject_requests",
    ]

    @admin.display(
        description="Requested role",
    )
    def role_name(self, obj):
        role = get_role(
            obj.requested_role
        )

        if role:
            return role.name

        return obj.requested_role

    @admin.action(
        description="Approve selected requests",
    )
    def approve_requests(
        self,
        request,
        queryset,
    ):
        approved_count = 0

        for access_request in queryset:
            try:
                AccessRequestService.approve_request(
                    access_request_id=access_request.id,
                    reviewed_by=request.user,
                )
                approved_count += 1

            except ValueError as exc:
                self.message_user(
                    request,
                    str(exc),
                    level=messages.WARNING,
                )

        if approved_count:
            self.message_user(
                request,
                f"{approved_count} access request(s) approved.",
                level=messages.SUCCESS,
            )

    @admin.action(
        description="Reject selected requests",
    )
    def reject_requests(
        self,
        request,
        queryset,
    ):
        rejected_count = 0

        for access_request in queryset:
            try:
                AccessRequestService.reject_request(
                    access_request_id=access_request.id,
                    reviewed_by=request.user,
                )
                rejected_count += 1

            except ValueError as exc:
                self.message_user(
                    request,
                    str(exc),
                    level=messages.WARNING,
                )

        if rejected_count:
            self.message_user(
                request,
                f"{rejected_count} access request(s) rejected.",
                level=messages.SUCCESS,
            )

    def has_add_permission(
        self,
        request,
    ):
        return False