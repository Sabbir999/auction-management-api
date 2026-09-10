"""
Custom user model for Firebase + Django hybrid authentication.

- Normal users:
    Authenticated through Firebase.
    firebase_uid is set.
    Django password is unusable.

- Staff users:
    Authenticated through Django Admin.
    is_staff=True.
    is_superuser=False.
    Permissions are assigned through Django Admin.

- Superusers:
    Authenticated through Django Admin.
    is_staff=True.
    is_superuser=True.
    Full platform access.
"""

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")

        email = self.normalize_email(email).lower()

        user = self.model(email=email, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)

        return user

    def create_user(self, email, password=None, **extra_fields):
        """
        Standard Django user creation method.
        """
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        return self._create_user(
            email=email,
            password=password,
            **extra_fields,
        )

    def create_firebase_user(self, email, firebase_uid, **extra_fields):
        """
        Create a normal Firebase-authenticated application user.
        """
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        extra_fields["firebase_uid"] = firebase_uid

        return self._create_user(
            email=email,
            password=None,
            **extra_fields,
        )

    def create_staff_user(self, email, password, **extra_fields):
        """
        Create an internal staff/developer account.
        """
        if not password:
            raise ValueError("Staff user must have a password.")

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", False)

        return self._create_user(
            email=email,
            password=password,
            **extra_fields,
        )

    def create_superuser(self, email, password, **extra_fields):
        """
        Create a Django superuser.
        """
        if not password:
            raise ValueError("Superuser must have a password.")

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(
                "Superuser must have is_staff=True."
            )

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(
                "Superuser must have is_superuser=True."
            )

        return self._create_user(
            email=email,
            password=password,
            **extra_fields,
        )


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    firebase_uid = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        help_text="Firebase UID. NULL for Django-only accounts.",
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    display_name = models.CharField(max_length=150, blank=True)
    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "auth_users"
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.email

    @property
    def is_firebase_user(self):
        return self.firebase_uid is not None


class AccessRequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class AccessRequest(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="access_requests",
    )
    requested_role = models.CharField(max_length=100)
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=AccessRequestStatus.choices,
        default=AccessRequestStatus.PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_access_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "access_requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "requested_role"],
                condition=models.Q(status=AccessRequestStatus.PENDING),
                name="unique_pending_access_request",
            ),
        ]

    def __str__(self):
        return f"{self.user_id} - {self.requested_role} ({self.status})"
