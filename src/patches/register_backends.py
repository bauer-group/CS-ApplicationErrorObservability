#!/usr/bin/env python3
"""
Backend Registration Patch for Bugsink v2
==========================================

This script patches Bugsink to register custom messaging backends
(Jira Cloud and GitHub Issues) during Docker image build.

Bugsink v2 registers backends in alerts/models.py via:
1. Import statements for backend classes
2. KIND_CHOICES in the MessagingServiceConfig.kind field
3. get_backend() method that returns the appropriate backend class

This script patches models.py to add our custom backends.
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
    # Find the existing backend import and add ours after it
    import_pattern = r'(from \.service_backends\.slack import SlackBackend)'

    if re.search(import_pattern, content):
        new_imports = '''from .service_backends.slack import SlackBackend
from .service_backends.jira_cloud import JiraCloudBackend
from .service_backends.github_issues import GitHubIssuesBackend'''
        content = re.sub(import_pattern, new_imports, content)
        print("  [OK] Added import statements")
    else:
        print("  [WARN] Could not find SlackBackend import")
        return False

    # === STEP B: Update kind choices ===
    # Find the kind field choices and add our backends
    choices_pattern = r'(kind = models\.CharField\(choices=\[)\("slack", "Slack \(or compatible\)"\),?\s*(\])'

    if re.search(choices_pattern, content):
        new_choices = '''kind = models.CharField(choices=[("slack", "Slack (or compatible)"), ("jira_cloud", "Jira Cloud"), ("github_issues", "GitHub Issues"), ]'''
        content = re.sub(choices_pattern, new_choices, content)
        print("  [OK] Updated kind choices")
    else:
        print("  [WARN] Could not find kind choices pattern")

    # === STEP C: Update get_backend() method ===
    # Find the get_backend method and add our backends
    get_backend_pattern = r'(def get_backend\(self\):)\s*(# once we have multiple backends: lookup by kind\.)\s*(return SlackBackend\(self\))'

    if re.search(get_backend_pattern, content):
        new_get_backend = '''def get_backend(self):
        if self.kind == "slack":
            return SlackBackend(self)
        if self.kind == "jira_cloud":
            return JiraCloudBackend(self)
        if self.kind == "github_issues":
            return GitHubIssuesBackend(self)
        raise ValueError(f"Unknown backend kind: {self.kind}")'''
        content = re.sub(get_backend_pattern, new_get_backend, content)
        print("  [OK] Updated get_backend() method")
    else:
        print("  [WARN] Could not find get_backend() method pattern")

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
    print("\n--- Patched models.py ---")
    with open(MODELS_FILE, "r", encoding="utf-8") as f:
        for i, line in enumerate(f.readlines(), 1):
            print(f"  {i:3}: {line.rstrip()}")
    print("--- End ---")


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

        # Show patched content for verification
        show_patched_content()

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
