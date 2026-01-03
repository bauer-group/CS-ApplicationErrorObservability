#!/usr/bin/env python3
"""
Backend Registration Patch for Bugsink v2
==========================================

This script patches Bugsink to register custom messaging backends
(Jira Cloud and GitHub Issues) during Docker image build.

Bugsink registers backends in alerts/models.py via:
1. Import statements for backend classes
2. get_alert_service_kind_choices() - returns list of (kind, display_name) tuples
3. get_alert_service_backend_class(kind) - factory function mapping kind to class

This script patches models.py to add our custom backends.
"""

import os
import sys
import re
import traceback

# Paths
ALERTS_DIR = "/app/alerts"
SERVICE_BACKENDS_DIR = os.path.join(ALERTS_DIR, "service_backends")
MODELS_FILE = os.path.join(ALERTS_DIR, "models.py")


def verify_backend_files():
    """Verify that our backend files were copied."""
    print("Step 1: Verifying backend files...")

    jira_file = os.path.join(SERVICE_BACKENDS_DIR, "jira_cloud.py")
    github_file = os.path.join(SERVICE_BACKENDS_DIR, "github_issues.py")

    jira_ok = os.path.exists(jira_file)
    github_ok = os.path.exists(github_file)

    print(f"  jira_cloud.py: {'OK' if jira_ok else 'MISSING'}")
    print(f"  github_issues.py: {'OK' if github_ok else 'MISSING'}")

    return jira_ok and github_ok


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
    if "jira_cloud" in content or "JiraCloudBackend" in content:
        print("  [OK] Already patched")
        return True

    original_content = content

    # === STEP A: Add imports ===
    # Find the last backend import and add ours after it
    import_pattern = r'(from \.service_backends\.(?:slack|discord|mattermost) import \w+Backend)'

    import_matches = list(re.finditer(import_pattern, content))
    if import_matches:
        last_import = import_matches[-1]
        insert_pos = last_import.end()

        new_imports = """
from .service_backends.jira_cloud import JiraCloudBackend
from .service_backends.github_issues import GitHubIssuesBackend"""

        content = content[:insert_pos] + new_imports + content[insert_pos:]
        print("  [OK] Added import statements")
    else:
        print("  [WARN] Could not find backend imports, trying alternative...")
        # Fallback: add after all imports
        if "from .service_backends" in content:
            # Find the service_backends import section
            lines = content.split('\n')
            insert_idx = 0
            for i, line in enumerate(lines):
                if 'from .service_backends' in line:
                    insert_idx = i + 1

            lines.insert(insert_idx, "from .service_backends.jira_cloud import JiraCloudBackend")
            lines.insert(insert_idx + 1, "from .service_backends.github_issues import GitHubIssuesBackend")
            content = '\n'.join(lines)
            print("  [OK] Added import statements (fallback)")

    # === STEP B: Update get_alert_service_kind_choices() ===
    # Find the function and add our choices
    choices_pattern = r'(def get_alert_service_kind_choices\(\):.*?return\s*\[)(.*?)(\])'

    def add_choices(match):
        prefix = match.group(1)
        existing = match.group(2)
        suffix = match.group(3)

        # Add our choices
        new_choices = '''
        ("jira_cloud", "Jira Cloud"),
        ("github_issues", "GitHub Issues"),
    '''
        return prefix + existing.rstrip().rstrip(',') + ',' + new_choices + suffix

    content, count = re.subn(choices_pattern, add_choices, content, flags=re.DOTALL)
    if count > 0:
        print("  [OK] Updated get_alert_service_kind_choices()")
    else:
        print("  [WARN] Could not find get_alert_service_kind_choices()")

    # === STEP C: Update get_alert_service_backend_class() ===
    # Find the function and add our backends before the raise statement
    backend_class_pattern = r'(def get_alert_service_backend_class\(kind\):.*?)(raise ValueError)'

    def add_backends(match):
        existing = match.group(1)
        raise_stmt = match.group(2)

        new_backends = '''    if kind == "jira_cloud":
        return JiraCloudBackend
    if kind == "github_issues":
        return GitHubIssuesBackend
    '''
        return existing + new_backends + raise_stmt

    content, count = re.subn(backend_class_pattern, add_backends, content, flags=re.DOTALL)
    if count > 0:
        print("  [OK] Updated get_alert_service_backend_class()")
    else:
        print("  [WARN] Could not find get_alert_service_backend_class()")

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


def show_file_snippet(filepath, start_pattern, lines=20):
    """Show a snippet of a file starting from a pattern."""
    if not os.path.exists(filepath):
        return

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(start_pattern, content)
    if match:
        start = content.rfind('\n', 0, match.start()) + 1
        end = start
        for _ in range(lines):
            next_newline = content.find('\n', end + 1)
            if next_newline == -1:
                break
            end = next_newline

        print(f"\n--- Snippet from {filepath} ---")
        snippet = content[start:end]
        for i, line in enumerate(snippet.split('\n'), 1):
            print(f"  {i:3}: {line}")
        print("--- End snippet ---")


def main():
    print("=" * 60)
    print("Bugsink Custom Backend Registration")
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

        # Show relevant snippets for verification
        show_file_snippet(MODELS_FILE, r"def get_alert_service_kind_choices", 15)
        show_file_snippet(MODELS_FILE, r"def get_alert_service_backend_class", 20)

        print("\n" + "=" * 60)
        print("[SUCCESS] Backend registration complete!")
        print()
        print("Added backends:")
        print("  - Jira Cloud (jira_cloud)")
        print("  - GitHub Issues (github_issues)")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FATAL ERROR] {type(e).__name__}: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
