# ULTRON Command System 2.0 — Phase 1

**Version:** 2.0  
**Implementation scope:** Command registry, prefix parser, conflict directives, and standard-mode selection.

## Scope boundary

Phase 1 provides deterministic parsing only. It does not execute user tasks, route work to agents, call external services, enforce account permissions, or authorise transactions. Those responsibilities belong to later execution and agent-routing layers. A parsed command is an instruction hint, never an approval token.

## Python interface

Use `parse_command(message: str) -> CommandRequest` from `ultron.commands`.

```python
from ultron.commands import parse_command

request = parse_command("/research /expert Investigate the UK market")

print(request.mode)                 # "command"
print(request.commands)             # ("research", "expert")
print(request.command_groups)      # ("research", "leadership")
print(request.task)                 # "Investigate the UK market"
print(request.conflict_resolutions) # ()
```

The returned `CommandRequest` is immutable. Commands are canonical lowercase names. Repeated commands are deduplicated while retaining their first-seen order.

## Registered commands

| Group | Commands |
|---|---|
| Leadership | `/ceo`, `/strategy`, `/expert`, `/critic`, `/compare`, `/brainstorm`, `/motivate` |
| Research | `/research`, `/seo`, `/eli5`, `/teacher`, `/explaincode`, `/summarize`, `/translate` |
| Writing | `/human`, `/email`, `/copywriter`, `/coverletter`, `/interview`, `/improve`, `/viral` |
| Technical | `/code`, `/debug`, `/promptengineer` |
| Formatting | `/brief`, `/expand`, `/list`, `/table`, `/outline`, `/simplify` |

Commands are recognised only as consecutive prefix tokens. Matching is case-insensitive. Slash text later in the task is ordinary task content.

## Standard mode

A message without a recognised prefix command returns `mode="standard"`, an empty command tuple, and the original trimmed message as its task.

## Conflict resolution

The parser retains all requested commands and adds stable conflict identifiers plus human-readable directives. It does not silently discard either command.

| Combination | Resolution identifier | Directive |
|---|---|---|
| `/brief /expand` | `brief_expand` | Provide a concise but sufficiently detailed answer. |
| `/expert /eli5` | `expert_eli5` | Retain technical accuracy while explaining simply. |
| `/critic /motivate` | `critic_motivate` | Identify weaknesses and provide constructive next steps. |
| `/table /list` | `table_list` | Use a table for comparisons and lists for actions. |
| `/human /expert` | `human_expert` | Use natural language without sacrificing technical precision. |
| `/research /brief` | `research_brief` | Investigate thoroughly but report only the essential findings. |

Read `request.conflict_resolutions` for identifiers and `request.conflict_directives` for their corresponding instructions. Unlisted combinations remain intact and do not produce a conflict directive.

The global instruction-priority contract is exposed as `INSTRUCTION_PRIORITY`:

1. Safety and platform rules.
2. Explicit user instructions and approval requirements.
3. Task-specific requirements.
4. Research and accuracy.
5. Output format.
6. Style.

The parser exposes this order; an execution host must enforce it.

## Unknown and malformed prefixes

- An unregistered command as the first token raises `UnknownCommandError`.
- A malformed first command token raises `ValueError`.
- After at least one valid command, the first unregistered slash token begins the task text. This allows task content such as a path to remain intact rather than being interpreted as an additional mode.
- Non-string input raises `TypeError`.

## Safety and execution boundary

The command parser never grants permission. In particular, `/ceo`, `/expert`, and any other command cannot authorise spending, transfers, purchases, account changes, credential access, external communications, publishing, customer transactions, fulfilment, dispatch, or destructive actions.

The caller must separately apply the ULTRON approval policy, validate dependencies, route the task to an authorised agent, execute only permitted actions, and verify the resulting evidence.

## Verification

The repository CI workflow runs:

```bash
ruff check .
pytest -q
python scripts/validate_repository.py
```

The command-parser tests cover standard mode, single and combined commands, case handling, duplicate removal, all six documented conflicts, unknown and malformed prefixes, non-string input, registry completeness, and slash text inside ordinary task content.

Passing Phase 1 tests establishes parser behavior only. It does not establish agent routing, approval enforcement, production execution, or autonomous operation.
