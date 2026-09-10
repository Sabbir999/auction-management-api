from dataclasses import dataclass


@dataclass(frozen=True)
class RoleDefinition:
    key: str
    name: str
    description: str
    permissions: tuple[str, ...]
    requestable: bool = True


PLAYER_PERMISSIONS = (
    "players.view_player",
    "players.add_player",
    "players.change_player",
    "players.delete_player",
)


ROLE_DEFINITIONS = {
    "player_manager": RoleDefinition(
        key="player_manager",
        name="Player Manager",
        description="Can create, update, and deactivate players.",
        permissions=PLAYER_PERMISSIONS,
    ),

    "application_admin": RoleDefinition(
        key="application_admin",
        name="Application Admin",
        description="Can manage Draftboard application data.",
        permissions=PLAYER_PERMISSIONS,
    ),
}


def get_role(role_key: str) -> RoleDefinition | None:
    return ROLE_DEFINITIONS.get(role_key)


def get_requestable_roles() -> list[RoleDefinition]:
    return [
        role
        for role in ROLE_DEFINITIONS.values()
        if role.requestable
    ]