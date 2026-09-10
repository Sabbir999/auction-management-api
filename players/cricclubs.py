import re
from urllib.parse import urlsplit, urlunsplit

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from players.models import (
    BattingStyle,
    BowlingStyle,
    Player,
    PlayerCareerStats,
    PlayerExternalSource,
    PlayerRole,
)


class CricClubsSyncService:
    @staticmethod
    def clean_player_name(
        player_name: str,
    ) -> str:
        player_name = (
            player_name
            or ""
        ).strip()

        player_name = re.sub(
            r"\s*CC Player ID\s*:?\s*\d+.*$",
            "",
            player_name,
            flags=re.IGNORECASE,
        )

        return player_name.strip()

    @classmethod
    def split_name(
        cls,
        player_name: str,
    ) -> tuple[str, str]:
        player_name = cls.clean_player_name(
            player_name
        )

        parts = player_name.split(
            maxsplit=1
        )

        first_name = (
            parts[0]
            if parts
            else ""
        )

        last_name = (
            parts[1]
            if len(parts) > 1
            else ""
        )

        return first_name, last_name

    @staticmethod
    def parse_integer(value):
        if value in (
            None,
            "",
            "-",
        ):
            return None

        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def canonical_profile_url(
        profile_url: str,
    ) -> str:
        if not profile_url:
            return ""

        parsed = urlsplit(
            profile_url
        )

        return urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                "",
                "",
            )
        )

    @staticmethod
    def map_player_role(
        value: str,
    ) -> str:
        value = (
            value
            or ""
        ).lower().strip()

        if (
            "wicket" in value
            and "batter" in value
        ):
            return (
                PlayerRole
                .WICKET_KEEPER_BATTER
            )

        if "wicket" in value:
            return (
                PlayerRole
                .WICKET_KEEPER
            )

        if (
            "all" in value
            and "round" in value
        ):
            return (
                PlayerRole
                .ALL_ROUNDER
            )

        if "bowl" in value:
            return PlayerRole.BOWLER

        if "bat" in value:
            return PlayerRole.BATTER

        return PlayerRole.ALL_ROUNDER

    @staticmethod
    def map_batting_style(
        value: str,
    ) -> str:
        value = (
            value
            or ""
        ).lower().strip()

        if "right" in value:
            return (
                BattingStyle
                .RIGHT_HANDED
            )

        if "left" in value:
            return (
                BattingStyle
                .LEFT_HANDED
            )

        return ""

    @staticmethod
    def map_bowling_style(
        value: str,
    ) -> str:
        value = (
            value
            or ""
        ).lower().strip()

        if value in (
            "",
            "-",
            "none",
            "does not bowl",
        ):
            return BowlingStyle.NONE

        mappings = (
            (
                ("right", "fast"),
                BowlingStyle.RIGHT_ARM_FAST,
            ),
            (
                ("right", "medium"),
                BowlingStyle.RIGHT_ARM_MEDIUM,
            ),
            (
                ("right", "off"),
                BowlingStyle.RIGHT_ARM_OFF_BREAK,
            ),
            (
                ("right", "leg"),
                BowlingStyle.RIGHT_ARM_LEG_BREAK,
            ),
            (
                ("left", "fast"),
                BowlingStyle.LEFT_ARM_FAST,
            ),
            (
                ("left", "medium"),
                BowlingStyle.LEFT_ARM_MEDIUM,
            ),
            (
                ("left", "orthodox"),
                BowlingStyle.LEFT_ARM_ORTHODOX,
            ),
            (
                ("left", "off"),
                BowlingStyle.LEFT_ARM_ORTHODOX,
            ),
            (
                ("left", "wrist"),
                BowlingStyle.LEFT_ARM_WRIST_SPIN,
            ),
            (
                ("left", "leg"),
                BowlingStyle.LEFT_ARM_WRIST_SPIN,
            ),
        )

        for keywords, style in mappings:
            if all(
                keyword in value
                for keyword in keywords
            ):
                return style

        return BowlingStyle.NONE

    @transaction.atomic
    def sync_player(
        self,
        data: dict,
    ) -> tuple[Player, bool]:
        cricclubs_id = str(
            data.get(
                "ccPlayerId"
            )
            or ""
        ).strip()

        profile_key = str(
            data.get(
                "profileKey"
            )
            or ""
        ).strip()

        profile_url = (
            self.canonical_profile_url(
                data.get(
                    "profileUrl",
                    "",
                )
            )
        )

        player_name = (
            self.clean_player_name(
                data.get(
                    "playerName",
                    ""
                )
            )
        )

        if not cricclubs_id:
            raise ValueError(
                "ccPlayerId is required."
            )

        if not profile_key:
            raise ValueError(
                "profileKey is required."
            )

        if not profile_url:
            raise ValueError(
                "profileUrl is required."
            )

        if not player_name:
            raise ValueError(
                "playerName is required."
            )

        sources = list(
            PlayerExternalSource
            .objects
            .select_related(
                "player"
            )
            .filter(
                Q(
                    cricclubs_id=
                    cricclubs_id
                )
                | Q(
                    profile_key=
                    profile_key
                )
            )[:2]
        )

        if len(sources) > 1:
            raise ValueError(
                (
                    "Conflicting CricClubs "
                    "source records found."
                )
            )

        source = (
            sources[0]
            if sources
            else None
        )

        first_name, last_name = (
            self.split_name(
                player_name
            )
        )

        player_data = {
            "first_name":
                first_name,

            "last_name":
                last_name,

            "player_role":
                self.map_player_role(
                    data.get(
                        "playingRole"
                    )
                ),

            "batting_style":
                self.map_batting_style(
                    data.get(
                        "battingStyle"
                    )
                ),

            "bowling_style":
                self.map_bowling_style(
                    data.get(
                        "bowlingStyle"
                    )
                ),

            "jersey_number":
                self.parse_integer(
                    data.get(
                        "jerseyNumber"
                    )
                ),
        }

        profile_image_url = (
            data.get(
                "profileImageUrl"
            )
            or ""
        ).strip()

        if profile_image_url:
            player_data[
                "profile_image_url"
            ] = profile_image_url

        michigan_team = (
            data.get(
                "michiganCricketAssociationTeam"
            )
            or ""
        ).strip()

        if michigan_team:
            player_data[
                "michigan_cricket_association_team"
            ] = michigan_team

        bd_community_cup_team = (
            data.get(
                "lastBdCommunityCupTeam"
            )
            or ""
        ).strip()

        if bd_community_cup_team:
            player_data[
                "last_bd_community_cup_team"
            ] = bd_community_cup_team

        created = False

        if source:
            player = source.player

            for (
                field,
                value,
            ) in player_data.items():
                setattr(
                    player,
                    field,
                    value,
                )

            player.save(
                update_fields=[
                    *player_data.keys(),
                    "updated_at",
                ]
            )

        else:
            player = (
                Player.objects.create(
                    **player_data
                )
            )

            source = (
                PlayerExternalSource
                .objects
                .create(
                    player=player,
                    cricclubs_id=(
                        cricclubs_id
                    ),
                    profile_key=(
                        profile_key
                    ),
                    profile_url=(
                        profile_url
                    ),
                )
            )

            created = True

        source.cricclubs_id = (
            cricclubs_id
        )

        source.profile_key = (
            profile_key
        )

        source.profile_url = (
            profile_url
        )

        source.last_synced_at = (
            timezone.now()
        )

        source.save(
            update_fields=[
                "cricclubs_id",
                "profile_key",
                "profile_url",
                "last_synced_at",
                "updated_at",
            ]
        )

        self.sync_career_stats(
            player=player,
            career_stats=data.get(
                "careerStats"
            ),
        )

        return player, created

    @staticmethod
    def sync_career_stats(
        player: Player,
        career_stats: dict | None,
    ):
        if not career_stats:
            return

        (
            PlayerCareerStats
            .objects
            .update_or_create(
                player=player,
                defaults={
                    "matches":
                        career_stats.get(
                            "matches",
                            0,
                        ),

                    "runs":
                        career_stats.get(
                            "runs",
                            0,
                        ),

                    "wickets":
                        career_stats.get(
                            "wickets",
                            0,
                        ),
                },
            )
        )