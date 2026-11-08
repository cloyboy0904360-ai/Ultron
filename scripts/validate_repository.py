from pathlib import Path

REQUIRED_PATHS = [
    ".github/copilot-instructions.md",
    "SECURITY.md",
    "docs/ARCHITECTURE.md",
    "docs/MASTER_AUDIT.md",
    "docs/EXECUTION_STATUS.md",
    "docs/MASTER_CONTROL_DASHBOARD.md",
    "docs/ASSET_AUDIT.md",
    "docs/TASK_REGISTER.md",
    "docs/AGENT_NETWORK.md",
    "docs/CONTROLLER.md",
    "docs/ASSET_REGISTRY.md",
    "docs/FULFILMENT_LIFECYCLE.md",
]


def main() -> None:
    root = Path(__file__).resolve().parents[1]

    missing = [p for p in REQUIRED_PATHS if not (root / p).exists()]
    if missing:
        raise SystemExit(f"Missing required files: {', '.join(missing)}")

    readme = (root / "README.md").read_text(encoding="utf-8").lower()
    if "type `18`" in readme or "authorize chatgpt" in readme:
        raise SystemExit("README contains invalid authorization instructions.")

    print("Repository validation checks passed.")


if __name__ == "__main__":
    main()
