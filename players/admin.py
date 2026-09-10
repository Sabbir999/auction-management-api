from django.contrib import admin

from players.models import Player, PlayerCareerStats, PlayerExternalSource


class PlayerCareerStatsInline(admin.StackedInline):
    model = PlayerCareerStats
    extra = 0
    max_num = 1
    fields = ("matches", "runs", "wickets", "updated_at")
    readonly_fields = ("updated_at",)


class PlayerExternalSourceInline(admin.StackedInline):
    model = PlayerExternalSource
    extra = 0
    max_num = 1
    fields = ("cricclubs_id", "profile_key", "profile_url", "last_synced_at", "created_at", "updated_at")
    readonly_fields = ("last_synced_at", "created_at", "updated_at")


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("id", "player_name", "player_role", "michigan_cricket_association_team", "last_bd_community_cup_team", "batting_style", "bowling_style", "jersey_number", "is_active", "created_at")
    list_filter = ("player_role", "batting_style", "bowling_style", "is_active")
    search_fields = ("first_name", "last_name", "michigan_cricket_association_team", "last_bd_community_cup_team", "cricclubs_source__cricclubs_id")
    ordering = ("first_name", "last_name")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("user",)
    list_select_related = ("user",)

    fieldsets = (
        ("Player", {"fields": ("user", "first_name", "last_name", "profile_image_url")}),
        ("Cricket Profile", {"fields": ("player_role", "batting_style", "bowling_style", "jersey_number")}),
        ("Teams", {"fields": ("michigan_cricket_association_team", "last_bd_community_cup_team")}),
        ("Additional Information", {"fields": ("bio", "is_active")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    inlines = [PlayerExternalSourceInline, PlayerCareerStatsInline]

    @admin.display(description="Player", ordering="first_name")
    def player_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"