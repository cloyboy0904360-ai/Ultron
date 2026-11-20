# ULTRON Command System 2.0 — Phase 1

**Version:** 2.0  
**Implementation scope:** Command registry, prefix parser, conflict directives, standard-mode selection, and integration with the GitHub Issues worker.

## Runtime connection

The GitHub Actions worker imports `parse_command` from `ultron.commands` before parsing the structured task block. Recognised commands and conflict metadata are included in the worker's evidence comment. Unknown or malformed first prefixes fail closed before an agent handler is invoked.

The live execution path is:

1. An authorised GitHub issue is created or labelled.
2. The issue body is parsed for zero or more registered prefix commands.
3. The worker extracts the fenced `ultron-task` JSON block.
4. The single `agent:<name>` issue label selects one of NOVA, FORGE, SALES, OPS, FINANCE, or PIXEL.
5. The agent's operation allowlist validates and executes the task.
6. The worker records command metadata, result evidence, and the lifecycle status in issue comments/labels.

The slash command does not select or override the agent. The issue must have exactly one agent label and `status:ready`. The operation must be in that agent's allowlist.

## Important capability boundary

This is a live GitHub Issues + GitHub Actions command interface, not a connection to ChatGPT's internal conversation runtime. The current six handlers are deterministic Python operations. They do not call an LLM or interpret the natural-language description. Slash commands are parsed and recorded as metadata; the fenced JSON operation and input are the executable contract. A model provider and credentials have not been connected.

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

The GitHub worker separately enforces the agent operation allowlist. Existing handler limits remain unchanged: SALES only drafts and never sends; PIXEL only prepares listings and never publishes; OPS checks evidence and never dispatches; FINANCE calculates and reconciles only; FORGE prepares technical review material and does not merge/deploy; NOVA creates bounded plans and cannot approve restricted actions.

## Issue submission

See `docs/GITHUB_ACTIONS_RUNTIME.md` for the live issue format. Every executable issue requires:
- One authorised issue author (owner, collaborator, or member).
- Exactly one `agent:<name>` label.
- The `status:ready` label.
- A valid `ultron-task` JSON block with exactly `operation` and `input`.
- An operation allowlisted for the selected agent.

A slash command prefix is optional. When supplied, it is parsed and captured in the evidence record.

## Verification

The repository CI workflow runs:

```bash
ruff check .
pytest -q
python scripts/validate_repository.py
```

The command-parser tests cover standard mode, single and combined commands, case handling, duplicate removal, all six documented conflicts, unknown and malformed prefixes, non-string input, registry completeness, and slash text inside ordinary task content. Worker integration tests cover command evidence capture and safe rejection of unknown prefixes.

Passing CI establishes the tested repository behaviour only. It does not establish a ChatGPT internal runtime connection, LLM-powered agents, production commerce execution, or continuous always-on operation.
