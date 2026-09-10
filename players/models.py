from django.conf import settings
from django.db import models


class PlayerRole(models.TextChoices):
    BATTER = "batter", "Batter"
    BOWLER = "bowler", "Bowler"
    ALL_ROUNDER = "all_rounder", "All-rounder"
    WICKET_KEEPER = "wicket_keeper", "Wicket-keeper"
    WICKET_KEEPER_BATTER = "wicket_keeper_batter", "Wicket-keeper Batter"


class BattingStyle(models.TextChoices):
    RIGHT_HANDED = "right_handed", "Right-handed"
    LEFT_HANDED = "left_handed", "Left-handed"


class BowlingStyle(models.TextChoices):
    RIGHT_ARM_FAST = "right_arm_fast", "Right-arm Fast"
    RIGHT_ARM_MEDIUM = "right_arm_medium", "Right-arm Medium"
    RIGHT_ARM_OFF_BREAK = "right_arm_off_break", "Right-arm Off Break"
    RIGHT_ARM_LEG_BREAK = "right_arm_leg_break", "Right-arm Leg Break"

    LEFT_ARM_FAST = "left_arm_fast", "Left-arm Fast"
    LEFT_ARM_MEDIUM = "left_arm_medium", "Left-arm Medium"
    LEFT_ARM_ORTHODOX = "left_arm_orthodox", "Left-arm Orthodox"
    LEFT_ARM_WRIST_SPIN = "left_arm_wrist_spin", "Left-arm Wrist Spin"

    NONE = "none", "Does not bowl"


class Player(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="player_profile")
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    michigan_cricket_association_team = models.CharField(max_length=150, blank=True, default="",)
    last_bd_community_cup_team = models.CharField(max_length=150, blank=True, default="",)
    player_role = models.CharField(max_length=30, choices=PlayerRole.choices)
    batting_style = models.CharField(max_length=30, choices=BattingStyle.choices, blank=True)
    bowling_style = models.CharField(max_length=40, choices=BowlingStyle.choices, default=BowlingStyle.NONE)
    jersey_number = models.PositiveIntegerField(null=True, blank=True)
    profile_image_url = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "players"
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class PlayerCareerStats(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name="career_stats")
    matches = models.PositiveIntegerField(default=0)
    runs = models.PositiveIntegerField(default=0)
    wickets = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "player_career_stats"

    def __str__(self):
        return f"{self.player} Career Stats"


class PlayerExternalSource(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name="cricclubs_source")
    cricclubs_id = models.CharField(max_length=100, unique=True)
    profile_key = models.CharField(max_length=100, unique=True)
    profile_url = models.URLField()
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "player_cricclubs_sources"

    def __str__(self):
        return f"{self.player} - {self.cricclubs_id}"