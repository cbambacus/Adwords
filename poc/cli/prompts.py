"""
Step-by-step user interaction prompts for the pipeline CLI.

Handles pause-at-each-step flow with view/edit/regenerate/quit options.
"""

from __future__ import annotations

from rich.console import Console

console = Console()


def prompt_continue(extra_options: dict = None) -> str:
    """
    Pause and wait for user input.

    Standard options: Enter to continue, q to quit.
    extra_options: dict of key -> description for additional options.

    Returns the key pressed (lowercase).
    """
    console.print()
    options = []
    if extra_options:
        for key, desc in extra_options.items():
            options.append(f"[bold][{key}][/] {desc}")

    options.append("[bold][Enter][/] Continue")
    options.append("[bold][q][/] Quit")

    console.print("  " + "  ".join(options))
    console.print()

    try:
        choice = input("  > ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return "q"

    return choice if choice else ""


def prompt_publish() -> str:
    """
    Special prompt for the publish step with explicit confirmation.

    Returns 'p' for publish, 's' for save only, 'q' for quit.
    """
    console.print()
    console.print("  [bold][p][/] Publish to test account")
    console.print("  [bold][s][/] Save campaign JSON to file (skip publish)")
    console.print("  [bold][q][/] Quit")
    console.print()

    try:
        choice = input("  > ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return "q"

    return choice if choice else "s"
