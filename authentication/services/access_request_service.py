from django.db import IntegrityError, transaction
from django.utils import timezone

from authentication.models import AccessRequest, AccessRequestStatus
from authentication.services.role_service import RoleService


class AccessRequestService:
    @staticmethod
    def get_pending_request(access_request_id: int) -> AccessRequest:
        access_request = (
            AccessRequest.objects
            .select_for_update(of=("self",))
            .select_related("user")
            .filter(id=access_request_id)
            .first()
        )

        if not access_request:
            raise ValueError(
                "Access request does not exist."
            )

        if access_request.status != AccessRequestStatus.PENDING:
            raise ValueError(
                "Access request has already been reviewed."
            )

        return access_request

    @classmethod
    def has_pending_request(cls, user, role_key: str) -> bool:
        return AccessRequest.objects.filter(
            user=user,
            requested_role=role_key,
            status=AccessRequestStatus.PENDING,
        ).exists()

    @classmethod
    @transaction.atomic
    def create_request(cls, user, role_key: str, reason: str = "") -> AccessRequest:
        role = RoleService.get_role(role_key)

        if not role.requestable:
            raise ValueError("This role cannot be requested.")

        if RoleService.user_has_role(user, role_key):
            raise ValueError(f"You already have {role.name} access.")

        if cls.has_pending_request(user, role_key):
            raise ValueError("You already have a pending request for this role.")

        try:
            return AccessRequest.objects.create(
                user=user,
                requested_role=role_key,
                reason=reason.strip(),
            )
        except IntegrityError:
            raise ValueError("You already have a pending request for this role.")

    @classmethod
    @transaction.atomic
    def approve_request(cls, access_request_id: int, reviewed_by) -> AccessRequest:
        access_request = cls.get_pending_request(access_request_id)

        RoleService.assign_role(
            access_request.user,
            access_request.requested_role,
        )

        access_request.status = AccessRequestStatus.APPROVED
        access_request.reviewed_by = reviewed_by
        access_request.reviewed_at = timezone.now()

        access_request.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "updated_at",
            ]
        )

        return access_request

    @classmethod
    @transaction.atomic
    def reject_request(cls, access_request_id: int, reviewed_by) -> AccessRequest:
        access_request = cls.get_pending_request(access_request_id)

        access_request.status = AccessRequestStatus.REJECTED
        access_request.reviewed_by = reviewed_by
        access_request.reviewed_at = timezone.now()

        access_request.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "updated_at",
            ]
        )

        return access_request

    @staticmethod
    def get_user_requests(user):
        return (
            AccessRequest.objects.filter(user=user)
            .select_related("reviewed_by")
            .order_by("-created_at")
        )