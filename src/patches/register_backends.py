#!/usr/bin/env python3
"""
Backend Registration Patch for Bugsink v2
==========================================

This script patches Bugsink v2 to register the custom messaging backends
(Jira Cloud and GitHub Issues) during Docker image build.

Bugsink v2 uses:
- MessagingServiceConfig model (not MessagingService)
- Dynamic KIND_CHOICES via get_alert_service_kind_choices()
- BACKENDS dict in alerts/service_backends/__init__.py

This script is run once during Docker build and then removed.
"""

import os
import re
import sys

# Paths to patch
ALERTS_DIR = "/app/alerts"
SERVICE_BACKENDS_DIR = os.path.join(ALERTS_DIR, "service_backends")
INIT_FILE = os.path.join(SERVICE_BACKENDS_DIR, "__init__.py")


def verify_files():
    """Verify that backend files exist."""
    print("Verifying backend files...")

    jira_file = os.path.join(SERVICE_BACKENDS_DIR, "jira_cloud.py")
    github_file = os.path.join(SERVICE_BACKENDS_DIR, "github_issues.py")

    files_ok = True

    if os.path.exists(jira_file):
        print(f"  [OK] {jira_file}")
    else:
        print(f"  [MISSING] {jira_file}")
        files_ok = False

    if os.path.exists(github_file):
        print(f"  [OK] {github_file}")
    else:
        print(f"  [MISSING] {github_file}")
        files_ok = False

    return files_ok


def patch_init():
    """Register backends in __init__.py.

    Bugsink v2 uses a BACKENDS dict and get_alert_service_kind_choices() function
    to dynamically register backends.
    """
    print("Patching alerts/service_backends/__init__.py...")

    if not os.path.exists(INIT_FILE):
        print(f"  [ERROR] {INIT_FILE} not found")
        print("  Creating new __init__.py with all backends...")

        content = '''"""
Bugsink Messaging Service Backends

Extended with custom backends: Jira Cloud, GitHub Issues
"""

from .discord import DiscordBackend
from .mattermost import MattermostBackend
from .slack import SlackBackend
from .jira_cloud import JiraCloudBackend
from .github_issues import GitHubIssuesBackend


BACKENDS = {
    "discord": DiscordBackend,
    "mattermost": MattermostBackend,
    "slack": SlackBackend,
    "jira_cloud": JiraCloudBackend,
    "github_issues": GitHubIssuesBackend,
}


def get_alert_service_kind_choices():
    """Return choices for MessagingServiceConfig.kind field.

    This is a callable to avoid non-DB-affecting migrations for adding new kinds.
    """
    return [
        ("discord", "Discord"),
        ("mattermost", "Mattermost"),
        ("slack", "Slack"),
        ("jira_cloud", "Jira Cloud"),
        ("github_issues", "GitHub Issues"),
    ]


def get_backend(kind):
    """Get backend class by kind."""
    return BACKENDS.get(kind)
'''
        with open(INIT_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        print("  [OK] Created new __init__.py with all backends")
        return True

    # Read existing file
    with open(INIT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if already patched
    if "jira_cloud" in content and "github_issues" in content:
        print("  [OK] Already patched, skipping")
        return True

    original_content = content
    modified = False

    # Step 1: Add imports for new backends
    import_lines = """
from .jira_cloud import JiraCloudBackend
from .github_issues import GitHubIssuesBackend
"""

    # Find last import line and add after it
    import_patterns = [
        r'(from \.slack import SlackBackend)',
        r'(from \.mattermost import MattermostBackend)',
        r'(from \.discord import DiscordBackend)',
    ]

    for pattern in import_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, r'\1' + import_lines, content)
            modified = True
            print("  [OK] Added import statements")
            break

    if not modified:
        # Fallback: add imports at the beginning
        content = import_lines.strip() + "\n\n" + content
        modified = True
        print("  [OK] Added import statements (fallback)")

    # Step 2: Add to BACKENDS dict
    backends_addition = '''    "jira_cloud": JiraCloudBackend,
    "github_issues": GitHubIssuesBackend,
'''

    # Pattern to find BACKENDS dict and add before closing brace
    # Match the last entry before }
    backends_pattern = r'(BACKENDS\s*=\s*\{[^}]*"(?:slack|mattermost|discord)":\s*\w+Backend,?\s*)(})'

    if re.search(backends_pattern, content, re.DOTALL):
        content = re.sub(
            backends_pattern,
            r'\1' + backends_addition + r'\2',
            content,
            flags=re.DOTALL
        )
        print("  [OK] Added backends to BACKENDS dict")
    else:
        print("  [WARN] Could not find BACKENDS dict pattern")

    # Step 3: Add to get_alert_service_kind_choices() function
    choices_addition = '''        ("jira_cloud", "Jira Cloud"),
        ("github_issues", "GitHub Issues"),
'''

    # Pattern to find the choices list and add before closing bracket
    choices_pattern = r'(get_alert_service_kind_choices.*?return\s*\[[^\]]*\("(?:slack|mattermost|discord)",\s*"[^"]+"\),?\s*)(\])'

    if re.search(choices_pattern, content, re.DOTALL):
        content = re.sub(
            choices_pattern,
            r'\1' + choices_addition + r'\2',
            content,
            flags=re.DOTALL
        )
        print("  [OK] Added choices to get_alert_service_kind_choices()")
    else:
        print("  [WARN] Could not find get_alert_service_kind_choices() pattern")

    # Write the patched content
    if content != original_content:
        with open(INIT_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        print("  [OK] Successfully patched __init__.py")
        return True
    else:
        print("  [WARN] No changes made to __init__.py")
        return False


def verify_patch():
    """Verify the patch was applied correctly."""
    print("Verifying patch...")

    if not os.path.exists(INIT_FILE):
        print("  [ERROR] __init__.py not found")
        return False

    with open(INIT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    checks = [
        ("JiraCloudBackend import", "from .jira_cloud import JiraCloudBackend" in content),
        ("GitHubIssuesBackend import", "from .github_issues import GitHubIssuesBackend" in content),
        ("jira_cloud in BACKENDS", '"jira_cloud"' in content and "JiraCloudBackend" in content),
        ("github_issues in BACKENDS", '"github_issues"' in content and "GitHubIssuesBackend" in content),
    ]

    all_ok = True
    for name, passed in checks:
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {name}")
        if not passed:
            all_ok = False

    return all_ok


def main():
    print("=" * 60)
    print("Bugsink v2 Custom Backend Registration")
    print("=" * 60)
    print()

    if not os.path.exists(ALERTS_DIR):
        print(f"[ERROR] {ALERTS_DIR} not found")
        print("This script must be run inside a Bugsink container")
        sys.exit(1)

    success = True

    # Step 1: Verify backend files were copied
    if not verify_files():
        print()
        print("[ERROR] Backend files not found. Make sure COPY commands ran.")
        success = False

    print()

    # Step 2: Patch __init__.py to register backends
    if not patch_init():
        success = False

    print()

    # Step 3: Verify the patch
    if not verify_patch():
        success = False

    print()
    print("=" * 60)

    if success:
        print("[SUCCESS] Backend registration complete!")
        print()
        print("Added backends:")
        print("  - Jira Cloud (jira_cloud)")
        print("  - GitHub Issues (github_issues)")
        print()
        print("These backends will appear in the Bugsink UI under")
        print("Project Settings > Alerts > Add Messaging Service")
    else:
        print("[WARNING] Backend registration completed with issues.")
        print("Check the output above for details.")

    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
