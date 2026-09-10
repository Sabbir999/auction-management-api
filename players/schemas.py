from datetime import datetime
from typing import Optional

from ninja import Field, Schema

from players.models import BattingStyle, BowlingStyle, PlayerRole


# -----------------------------------
# Player Input Schemas
# -----------------------------------


class PlayerCreateSchema(Schema):
    first_name: str
    last_name: str
    michigan_cricket_association_team: str = ""
    last_bd_community_cup_team: str = ""
    player_role: PlayerRole
    batting_style: Optional[BattingStyle] = None
    bowling_style: BowlingStyle = BowlingStyle.NONE
    jersey_number: Optional[int] = Field(default=None, ge=0)
    profile_image_url: str = ""
    bio: str = ""


class PlayerUpdateSchema(Schema):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    michigan_cricket_association_team: Optional[str] = None
    last_bd_community_cup_team: Optional[str] = None
    player_role: Optional[PlayerRole] = None
    batting_style: Optional[BattingStyle] = None
    bowling_style: Optional[BowlingStyle] = None
    jersey_number: Optional[int] = Field(default=None, ge=0)
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: Optional[bool] = None


# -----------------------------------
# Career Stats Schemas
# -----------------------------------


class PlayerStatsUpdateSchema(Schema):
    matches: int = Field(default=0, ge=0)
    runs: int = Field(default=0, ge=0)
    wickets: int = Field(default=0, ge=0)


class PlayerStatsResponseSchema(Schema):
    id: int
    matches: int
    runs: int
    wickets: int
    updated_at: datetime


# -----------------------------------
# Player Response Schemas
# -----------------------------------


class PlayerResponseSchema(Schema):
    id: int
    first_name: str
    last_name: str
    michigan_cricket_association_team: str
    last_bd_community_cup_team: str
    player_role: str
    batting_style: Optional[str] = ""
    bowling_style: str
    jersey_number: Optional[int] = None
    profile_image_url: str
    bio: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PlayerDetailResponseSchema(PlayerResponseSchema):
    cricclubs_id: Optional[str] = None
    career_stats: Optional[PlayerStatsResponseSchema] = None


# -----------------------------------
# CricClubs Import Schemas
# -----------------------------------


class CricClubsCareerStatsSchema(Schema):
    matches: int = 0
    runs: int = 0
    wickets: int = 0


class CricClubsPlayerImportSchema(Schema):
    playerName: str
    ccPlayerId: str
    profileKey: str
    profileUrl: str
    profileImageUrl: str = ""
    michiganCricketAssociationTeam: str = ""
    lastBdCommunityCupTeam: str = ""
    playingRole: str = ""
    battingStyle: str = ""
    bowlingStyle: str = ""
    jerseyNumber: Optional[str] = None
    careerStats: CricClubsCareerStatsSchema


# -----------------------------------
# Generic Response
# -----------------------------------


class MessageResponseSchema(Schema):
    detail: str