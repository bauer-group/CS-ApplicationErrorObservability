#!/usr/bin/env python3
"""
Backend Registration Patch for Bugsink v2.x
===========================================

This script patches Bugsink to register custom messaging backends
during Docker image build.

Bugsink v2.x uses a modern architecture with:
1. Import statements for backend classes at the top
2. get_alert_service_kind_choices() function returning available backends
3. get_alert_service_backend_class(kind) function returning backend class

This script patches alerts/models.py to add our custom backends.

Compatible with: Bugsink 2.0.x+
Last updated: 2026
"""

import os
import sys
import re
import traceback

# Paths - Bugsink is installed as a Python package in site-packages
SITE_PACKAGES = "/usr/local/lib/python3.12/site-packages"
ALERTS_DIR = os.path.join(SITE_PACKAGES, "alerts")
SERVICE_BACKENDS_DIR = os.path.join(ALERTS_DIR, "service_backends")
MODELS_FILE = os.path.join(ALERTS_DIR, "models.py")

# Backend definitions: (module_name, class_name, kind, display_name)
BACKENDS = [
    ("jira_cloud", "JiraCloudBackend", "jira_cloud", "Jira Cloud"),
    ("github_issues", "GitHubIssuesBackend", "github_issues", "GitHub Issues"),
    ("microsoft_teams", "MicrosoftTeamsBackend", "microsoft_teams", "Microsoft Teams"),
    ("pagerduty", "PagerDutyBackend", "pagerduty", "PagerDuty"),
    ("webhook", "WebhookBackend", "webhook", "Webhook (Generic)"),
]


def verify_backend_files():
    """Verify that our backend files were copied."""
    print("Step 1: Verifying backend files...")

    all_ok = True
    for module_name, class_name, kind, display_name in BACKENDS:
        file_path = os.path.join(SERVICE_BACKENDS_DIR, f"{module_name}.py")
        exists = os.path.exists(file_path)
        print(f"  {module_name}.py: {'OK' if exists else 'MISSING'}")
        if not exists:
            all_ok = False

    return all_ok


def patch_models_file():
    """Patch alerts/models.py to register our backends."""
    print("\nStep 2: Patching alerts/models.py...")

    if not os.path.exists(MODELS_FILE):
        print(f"  [ERROR] {MODELS_FILE} does not exist!")
        return False

    with open(MODELS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"  Original file size: {len(content)} bytes")

    # Check if already patched
    if "jira_cloud" in content and "JiraCloudBackend" in content:
        print("  [OK] Already patched")
        return True

    original_content = content

    # === STEP A: Add imports ===
    # Find the last existing backend import and add ours after it
    # Current Bugsink has imports like:
    #   from .service_backends.slack import SlackBackend
    #   from .service_backends.mattermost import MattermostBackend
    #   from .service_backends.discord import DiscordBackend

    # Find the last backend import line
    import_pattern = r'(from \.service_backends\.\w+ import \w+Backend\n)(?=\n)'

    if re.search(import_pattern, content):
        # Build our import lines
        new_imports = ""
        for module_name, class_name, kind, display_name in BACKENDS:
            new_imports += f"from .service_backends.{module_name} import {class_name}\n"

        # Find position after last import
        matches = list(re.finditer(r'from \.service_backends\.\w+ import \w+Backend\n', content))
        if matches:
            last_match = matches[-1]
            insert_pos = last_match.end()
            content = content[:insert_pos] + new_imports + content[insert_pos:]
            print("  [OK] Added import statements")
        else:
            print("  [WARN] Could not find position for imports")
            return False
    else:
        print("  [WARN] Could not find backend import pattern")
        return False

    # === STEP B: Update get_alert_service_kind_choices() ===
    # Find the function and add our choices to the list
    # The function returns a list like: [("discord", "Discord"), ("slack", "Slack"), ...]

    choices_func_pattern = r'(def get_alert_service_kind_choices\(\):.*?return \[)(.*?)(\])'

    match = re.search(choices_func_pattern, content, re.DOTALL)
    if match:
        prefix = match.group(1)
        existing_choices = match.group(2)
        suffix = match.group(3)

        # Add our choices (sorted alphabetically)
        new_choices = existing_choices.rstrip().rstrip(',')
        for module_name, class_name, kind, display_name in BACKENDS:
            # Check if this choice already exists
            if f'"{kind}"' not in new_choices:
                new_choices += f',\n        ("{kind}", "{display_name}")'

        # Sort the choices alphabetically by kind
        # Extract all tuples, sort them, and rebuild
        choice_pattern = r'\("(\w+)", "([^"]+)"\)'
        all_choices = re.findall(choice_pattern, new_choices)
        all_choices = sorted(set(all_choices), key=lambda x: x[0])

        # Rebuild the choices list
        rebuilt_choices = "\n"
        for kind_val, display in all_choices:
            rebuilt_choices += f'        ("{kind_val}", "{display}"),\n'
        rebuilt_choices += "    "

        content = content[:match.start()] + prefix + rebuilt_choices + suffix + content[match.end():]
        print("  [OK] Updated get_alert_service_kind_choices()")
    else:
        print("  [WARN] Could not find get_alert_service_kind_choices() function")

    # === STEP C: Update get_alert_service_backend_class() ===
    # Find the function and add our backend mappings before the raise ValueError line
    # The function has: if kind == "slack": return SlackBackend

    # Find the raise ValueError line in get_alert_service_backend_class and insert before it
    # Pattern matches the indented raise ValueError line
    raise_pattern = r'(    raise ValueError\(f"Unknown backend kind:)'

    match = re.search(raise_pattern, content)
    if match:
        # Check which backends need to be added
        new_cases = ""
        for module_name, class_name, kind, display_name in BACKENDS:
            if f'if kind == "{kind}"' not in content:
                new_cases += f'    if kind == "{kind}":\n        return {class_name}\n'

        if new_cases:
            # Insert new cases before the raise statement
            insert_pos = match.start(1)
            content = content[:insert_pos] + new_cases + content[insert_pos:]
            print("  [OK] Updated get_alert_service_backend_class()")
        else:
            print("  [OK] get_alert_service_backend_class() already has all backends")
    else:
        print("  [WARN] Could not find raise ValueError in get_alert_service_backend_class()")

    # Write the patched content
    if content != original_content:
        with open(MODELS_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Patched file size: {len(content)} bytes")
        print("  [OK] models.py patched successfully")
        return True
    else:
        print("  [WARN] No changes made to models.py")
        return False


def verify_syntax():
    """Verify the patched file has valid Python syntax."""
    print("\nStep 3: Verifying Python syntax...")

    try:
        with open(MODELS_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        compile(content, MODELS_FILE, "exec")
        print("  [OK] Syntax is valid")
        return True

    except SyntaxError as e:
        print(f"  [ERROR] Syntax error: {e}")
        print(f"  Line {e.lineno}: {e.text}")
        return False


def show_patched_content():
    """Show the patched models.py content for verification."""
    print("\n--- Patched models.py (first 100 lines) ---")
    with open(MODELS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:100], 1):
            print(f"  {i:3}: {line.rstrip()}")
    if len(lines) > 100:
        print(f"  ... ({len(lines) - 100} more lines)")
    print("--- End ---")


def main():
    print("=" * 60)
    print("Bugsink Custom Backend Registration (v2.x compatible)")
    print("=" * 60)

    try:
        # Step 1: Verify backend files
        if not verify_backend_files():
            print("\n[ERROR] Backend files not found!")
            sys.exit(1)

        # Step 2: Patch models.py
        if not patch_models_file():
            print("\n[ERROR] Failed to patch models.py")
            sys.exit(1)

        # Step 3: Verify syntax
        if not verify_syntax():
            print("\n[ERROR] Patched file has syntax errors")
            sys.exit(1)

        # Show patched content for verification
        show_patched_content()

        print("\n" + "=" * 60)
        print("[SUCCESS] Backend registration complete!")
        print()
        print("Added backends:")
        for module_name, class_name, kind, display_name in BACKENDS:
            print(f"  - {display_name} ({kind})")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FATAL ERROR] {type(e).__name__}: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
