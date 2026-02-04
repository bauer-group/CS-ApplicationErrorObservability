#!/usr/bin/env python3
"""
Template Patch for Bugsink v2.x
===============================

This script was originally needed to patch the messaging service template
to add JavaScript that reloads the page when the backend dropdown changes.

IMPORTANT: Bugsink v2.x uses a new template architecture with:
- project_messaging_service_new.html for adding new services
- config_forms dictionary containing all backend forms
- JavaScript already handles backend switching

This patch is NO LONGER NEEDED for Bugsink 2.0.12 and later.
It now only verifies that the modern templates are in place.

Compatible with: Bugsink 2.0.12+
Last updated: 2026
"""

import os
import sys

# Paths
SITE_PACKAGES = "/usr/local/lib/python3.12/site-packages"
TEMPLATES_DIR = os.path.join(SITE_PACKAGES, "projects", "templates", "projects")
NEW_TEMPLATE = os.path.join(TEMPLATES_DIR, "project_messaging_service_new.html")
EDIT_TEMPLATE = os.path.join(TEMPLATES_DIR, "project_messaging_service_edit.html")


def verify_modern_templates():
    """Verify that Bugsink has the modern template architecture."""
    print("Verifying Bugsink template architecture...")

    # Check for new template (modern architecture)
    new_exists = os.path.exists(NEW_TEMPLATE)
    print(f"  project_messaging_service_new.html: {'OK' if new_exists else 'MISSING'}")

    # Check for edit template
    edit_exists = os.path.exists(EDIT_TEMPLATE)
    print(f"  project_messaging_service_edit.html: {'OK' if edit_exists else 'MISSING'}")

    if new_exists:
        with open(NEW_TEMPLATE, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for modern architecture indicators
        has_config_forms = "config_forms" in content
        print(f"  config_forms dictionary support: {'OK' if has_config_forms else 'MISSING'}")

        if has_config_forms:
            print("\n  [OK] Modern template architecture detected - no patching needed!")
            return True

    print("\n  [WARN] Older template architecture may be in use")
    return False


def main():
    print("=" * 60)
    print("Bugsink Template Patch - Architecture Verification")
    print("=" * 60)
    print()
    print("NOTE: Bugsink 2.0.12+ uses a new template system with")
    print("      multiple backend forms loaded at once.")
    print()

    if not verify_modern_templates():
        print("\n[WARNING] Templates may need manual patching for older Bugsink versions")
        print("See the original patch_template.py for the legacy patching logic")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("[SUCCESS] Template architecture verification complete!")
    print("No patching required for Bugsink 2.0.12+")
    print("=" * 60)


if __name__ == "__main__":
    main()
