import pytest

from ultron.commands import (
    COMMAND_GROUPS,
    UnknownCommandError,
    parse_command,
)


def test_standard_mode_is_used_without_a_prefix_command():
    request = parse_command("Review the current business plan")

    assert request.mode == "standard"
    assert request.commands == ()
    assert request.task == "Review the current business plan"


def test_single_command_is_case_insensitive_and_preserves_task():
    request = parse_command("  /CEO Review my business plan  ")

    assert request.commands == ("ceo",)
    assert request.command_groups == ("leadership",)
    assert request.task == "Review my business plan"
    assert request.mode == "command"


def test_multiple_commands_are_parsed_and_duplicates_removed_in_order():
    request = parse_command("/research /expert /research Investigate the market")

    assert request.commands == ("research", "expert")
    assert request.command_groups == ("research", "leadership")
    assert request.task == "Investigate the market"


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("/brief /expand Explain the design", ("brief_expand",)),
        ("/expert /eli5 Explain OAuth", ("expert_eli5",)),
        ("/critic /motivate Review this plan", ("critic_motivate",)),
        ("/table /list Compare suppliers", ("table_list",)),
        ("/human /expert Write a technical explanation", ("human_expert",)),
        ("/research /brief Investigate this issue", ("research_brief",)),
    ],
)
def test_documented_conflicts_produce_resolution_directives(message, expected):
    request = parse_command(message)

    assert request.conflict_resolutions == expected


def test_compatible_commands_do_not_create_a_conflict():
    request = parse_command("/ceo /strategy Review the roadmap")

    assert request.conflict_resolutions == ()


def test_unknown_prefix_command_is_rejected():
    with pytest.raises(UnknownCommandError, match="unknown command: /unknown"):
        parse_command("/unknown Do something")


def test_malformed_prefix_command_is_rejected():
    with pytest.raises(ValueError, match="malformed command"):
        parse_command("/123 Do something")


def test_non_string_input_is_rejected():
    with pytest.raises(TypeError, match="message must be a string"):
        parse_command(None)


def test_command_registry_contains_all_specified_commands():
    assert set(COMMAND_GROUPS) == {
        "ceo", "strategy", "expert", "critic", "compare", "brainstorm", "motivate",
        "research", "seo", "eli5", "teacher", "explaincode", "summarize", "translate",
        "human", "email", "copywriter", "coverletter", "interview", "improve", "viral",
        "code", "debug", "promptengineer",
        "brief", "expand", "list", "table", "outline", "simplify",
    }


def test_slash_text_inside_task_is_not_reinterpreted_as_a_command():
    request = parse_command("Please explain the /tmp/config.yaml path")

    assert request.mode == "standard"
    assert request.task == "Please explain the /tmp/config.yaml path"
