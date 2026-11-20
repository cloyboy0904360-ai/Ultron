"""Deterministic parser and registry for ULTRON prefix commands.

This module parses command prefixes into structured requests. It does not
execute tasks, route agents, grant permissions, or perform external actions.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

COMMAND_GROUPS: dict[str, str] = {
    "ceo": "leadership",
    "strategy": "leadership",
    "expert": "leadership",
    "critic": "leadership",
    "compare": "leadership",
    "brainstorm": "leadership",
    "motivate": "leadership",
    "research": "research",
    "seo": "research",
    "eli5": "research",
    "teacher": "research",
    "explaincode": "research",
    "summarize": "research",
    "translate": "research",
    "human": "writing",
    "email": "writing",
    "copywriter": "writing",
    "coverletter": "writing",
    "interview": "writing",
    "improve": "writing",
    "viral": "writing",
    "code": "technical",
    "debug": "technical",
    "promptengineer": "technical",
    "brief": "formatting",
    "expand": "formatting",
    "list": "formatting",
    "table": "formatting",
    "outline": "formatting",
    "simplify": "formatting",
}

COMMANDS = frozenset(COMMAND_GROUPS)

INSTRUCTION_PRIORITY = (
    "safety_and_platform_rules",
    "explicit_user_instructions_and_approval_requirements",
    "task_specific_requirements",
    "research_and_accuracy",
    "output_format",
    "style",
)

CONFLICT_RESOLUTIONS: dict[frozenset[str], str] = {
    frozenset({"brief", "expand"}): "brief_expand",
    frozenset({"expert", "eli5"}): "expert_eli5",
    frozenset({"critic", "motivate"}): "critic_motivate",
    frozenset({"list", "table"}): "table_list",
    frozenset({"human", "expert"}): "human_expert",
    frozenset({"research", "brief"}): "research_brief",
}

CONFLICT_DIRECTIVES: dict[str, str] = {
    "brief_expand": "Provide a concise but sufficiently detailed answer.",
    "expert_eli5": "Retain technical accuracy while explaining simply.",
    "critic_motivate": "Identify weaknesses and provide constructive next steps.",
    "table_list": "Use a table for comparisons and lists for actions.",
    "human_expert": "Use natural language without sacrificing technical precision.",
    "research_brief": "Investigate thoroughly but report only the essential findings.",
}

_COMMAND_PREFIX = re.compile(r"/([A-Za-z][A-Za-z0-9_-]*)(?=\s|$)")


class UnknownCommandError(ValueError):
    """Raised when the first command-like prefix is not registered."""


@dataclass(frozen=True)
class CommandRequest:
    """Parsed request; commands are canonical lowercase registry keys."""

    commands: tuple[str, ...]
    command_groups: tuple[str, ...]
    task: str
    mode: str
    conflict_resolutions: tuple[str, ...]

    @property
    def conflict_directives(self) -> tuple[str, ...]:
        """Human-readable instructions corresponding to detected conflicts."""
        return tuple(
            CONFLICT_DIRECTIVES[resolution]
            for resolution in self.conflict_resolutions
        )


def resolve_conflicts(commands: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Return all documented conflict rules triggered by the supplied commands."""
    selected = set(commands)
    return tuple(
        resolution
        for pair, resolution in CONFLICT_RESOLUTIONS.items()
        if pair.issubset(selected)
    )


def parse_command(message: str) -> CommandRequest:
    """Parse consecutive slash-command prefixes and return the remaining task.

    Commands are case-insensitive. Duplicate commands are removed while
    preserving their first occurrence. With no command prefix, standard mode
    is returned. Once at least one valid command has been parsed, the first
    unregistered slash token begins the task text rather than becoming a mode.
    """
    if not isinstance(message, str):
        raise TypeError("message must be a string")

    remaining = message.strip()
    commands: list[str] = []

    while remaining.startswith("/"):
        match = _COMMAND_PREFIX.match(remaining)
        if match is None:
            if not commands:
                raise ValueError("malformed command prefix")
            break

        command = match.group(1).lower()
        if command not in COMMANDS:
            if not commands:
                raise UnknownCommandError(f"unknown command: /{command}")
            break

        if command not in commands:
            commands.append(command)
        remaining = remaining[match.end():].lstrip()

    groups: list[str] = []
    for command in commands:
        group = COMMAND_GROUPS[command]
        if group not in groups:
            groups.append(group)

    command_tuple = tuple(commands)
    return CommandRequest(
        commands=command_tuple,
        command_groups=tuple(groups),
        task=remaining.strip(),
        mode="command" if command_tuple else "standard",
        conflict_resolutions=resolve_conflicts(command_tuple),
    )
