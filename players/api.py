import secrets
from typing import Optional

from django.conf import settings
from django.db.models import Q
from ninja import Router
from ninja.pagination import paginate
from ninja.security import APIKeyHeader

from authentication.auth import firebase_auth
from authentication.permissions import permission_required
from players.cricclubs import CricClubsSyncService
from players.models import Player, PlayerCareerStats, PlayerExternalSource
from players.schemas import (
    CricClubsPlayerImportSchema,
    MessageResponseSchema,
    PlayerCreateSchema,
    PlayerDetailResponseSchema,
    PlayerResponseSchema,
    PlayerStatsResponseSchema,
    PlayerStatsUpdateSchema,
    PlayerUpdateSchema,
)
from utils.pagination import CustomPagination

router = Router(tags=["Players"], auth=firebase_auth)


# -----------------------------------
# Helpers
# -----------------------------------


def get_player(player_id: int) -> Optional[Player]:
    return Player.objects.filter(id=player_id).first()


def serialize_career_stats(stats: Optional[PlayerCareerStats]) -> Optional[dict]:
    if not stats:
        return None

    return {
        "id": stats.id,
        "matches": stats.matches,
        "runs": stats.runs,
        "wickets": stats.wickets,
        "updated_at": stats.updated_at,
    }


def serialize_player(player: Player, include_details: bool = False) -> dict:
    data = {
        "id": player.id,
        "first_name": player.first_name,
        "last_name": player.last_name,
        "michigan_cricket_association_team": player.michigan_cricket_association_team,
        "last_bd_community_cup_team": player.last_bd_community_cup_team,
        "player_role": player.player_role,
        "batting_style": player.batting_style,
        "bowling_style": player.bowling_style,
        "jersey_number": player.jersey_number,
        "profile_image_url": player.profile_image_url,
        "bio": player.bio,
        "is_active": player.is_active,
        "created_at": player.created_at,
        "updated_at": player.updated_at,
    }

    if include_details:
        try:
            career_stats = player.career_stats
        except PlayerCareerStats.DoesNotExist:
            career_stats = None

        try:
            cricclubs_source = player.cricclubs_source
        except PlayerExternalSource.DoesNotExist:
            cricclubs_source = None

        data["career_stats"] = serialize_career_stats(career_stats)
        data["cricclubs_id"] = (
            cricclubs_source.cricclubs_id if cricclubs_source else None
        )

    return data


# -----------------------------------
# Create Player
# -----------------------------------


@router.post(
    "",
    summary="Create player",
    description="Creates a new cricket player profile.",
    response={201: PlayerResponseSchema},
)
@permission_required("players.add_player")
def create_player(request, payload: PlayerCreateSchema):
    player_data = payload.model_dump(mode="json", exclude_none=True)
    player = Player.objects.create(**player_data)
    return 201, serialize_player(player)


# -----------------------------------
# List Players
# -----------------------------------


@router.get(
    "",
    summary="List players",
    description="Returns players with search, filtering, and pagination.",
    response=list[PlayerResponseSchema],
)
@paginate(CustomPagination)
def list_players(request, search: str = "", player_role: str = "", team: str = "", active: bool = True):
    queryset = Player.objects.filter(is_active=active)

    if search:
        queryset = queryset.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(michigan_cricket_association_team__icontains=search)
            | Q(last_bd_community_cup_team__icontains=search)
        )

    if player_role:
        queryset = queryset.filter(player_role=player_role)

    if team:
        queryset = queryset.filter(
            Q(michigan_cricket_association_team__icontains=team)
            | Q(last_bd_community_cup_team__icontains=team)
        )

    return queryset.order_by("first_name", "last_name")


# -----------------------------------
# Player Detail
# -----------------------------------


@router.get(
    "/{player_id}",
    summary="Get player",
    description=(
        "Returns a player profile including career statistics and CricClubs ID."
    ),
    response={200: PlayerDetailResponseSchema, 404: MessageResponseSchema},
)
def get_player_detail(request, player_id: int):
    player = (
        Player.objects.select_related("career_stats", "cricclubs_source")
        .filter(id=player_id)
        .first()
    )

    if not player:
        return 404, {"detail": "Player does not exist."}

    return 200, serialize_player(player, include_details=True)


# -----------------------------------
# Update Player
# -----------------------------------


@router.patch(
    "/{player_id}",
    summary="Update player",
    description="Updates fields on an existing cricket player profile.",
    response={200: PlayerResponseSchema, 404: MessageResponseSchema},
)
def update_player(request, player_id: int, payload: PlayerUpdateSchema):
    player = get_player(player_id)

    if not player:
        return 404, {"detail": "Player does not exist."}

    update_data = payload.model_dump(mode="json", exclude_unset=True)
    blankable_fields = {
        "michigan_cricket_association_team",
        "last_bd_community_cup_team",
        "batting_style",
        "profile_image_url",
        "bio",
    }
    cleaned_update_data = {}

    for field, value in update_data.items():
        if value is not None:
            cleaned_update_data[field] = value
            continue

        if field == "jersey_number":
            cleaned_update_data[field] = None
            continue

        if field in blankable_fields:
            cleaned_update_data[field] = ""

    if not cleaned_update_data:
        return 200, serialize_player(player)

    for field, value in cleaned_update_data.items():
        setattr(player, field, value)

    player.save(update_fields=[*cleaned_update_data.keys(), "updated_at"])
    return 200, serialize_player(player)


# -----------------------------------
# Deactivate Player
# -----------------------------------


@router.delete(
    "/{player_id}",
    summary="Deactivate player",
    description="Deactivates a player instead of permanently deleting the record.",
    response={200: MessageResponseSchema, 404: MessageResponseSchema},
)
@permission_required("players.delete_player")
def deactivate_player(request, player_id: int):
    player = get_player(player_id)

    if not player:
        return 404, {"detail": "Player does not exist."}

    if not player.is_active:
        return 200, {"detail": "Player is already inactive."}

    player.is_active = False
    player.save(update_fields=["is_active", "updated_at"])
    return 200, {"detail": "Player deactivated successfully."}


# -----------------------------------
# Career Stats
# -----------------------------------


@router.put(
    "/{player_id}/stats",
    summary="Create or update career stats",
    description="Creates or updates the player's overall career statistics.",
    response={200: PlayerStatsResponseSchema, 404: MessageResponseSchema},
)
@permission_required("players.change_player")
def update_player_stats(request, player_id: int, payload: PlayerStatsUpdateSchema):
    player = get_player(player_id)

    if not player:
        return 404, {"detail": "Player does not exist."}

    stats, _ = PlayerCareerStats.objects.update_or_create(
        player=player,
        defaults=payload.model_dump(mode="json"),
    )
    return 200, serialize_career_stats(stats)


# -----------------------------------
# CricClubs Import Auth
# -----------------------------------


class CricClubsImportAuth(APIKeyHeader):
    param_name = "X-CricClubs-Import-Key"

    def authenticate(self, request, key):
        if not key or not settings.CRICCLUBS_IMPORT_KEY:
            return None

        if secrets.compare_digest(key, settings.CRICCLUBS_IMPORT_KEY):
            return key

        return None


cricclubs_import_auth = CricClubsImportAuth()


# -----------------------------------
# CricClubs Import
# -----------------------------------


@router.post(
    "/cricclubs/import",
    auth=cricclubs_import_auth,
    summary="Import CricClubs player",
    description="Creates or updates a player using scraped CricClubs profile data.",
    response={200: MessageResponseSchema, 400: MessageResponseSchema},
)
def import_cricclubs_player(request, payload: CricClubsPlayerImportSchema):
    try:
        player, created = CricClubsSyncService().sync_player(
            payload.model_dump(mode="json")
        )
    except ValueError as exc:
        return 400, {"detail": str(exc)}

    action = "Created" if created else "Updated"
    return 200, {
        "detail": f"{action}: {player.first_name} {player.last_name}"
    }