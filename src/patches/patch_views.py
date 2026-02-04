#!/usr/bin/env python3
"""
Views Patch for Bugsink v2.x
============================

This script was originally needed to patch projects/views.py to dynamically
load the correct ConfigForm based on the selected backend kind.

IMPORTANT: Bugsink v2.x already includes dynamic form loading via:
- get_alert_service_backend_class(kind).get_form_class()

This patch is NO LONGER NEEDED for Bugsink 2.0.12 and later.
It now only verifies that the modern architecture is in place.

Compatible with: Bugsink 2.0.12+
Last updated: 2026
"""

import os
import sys

# Paths
SITE_PACKAGES = "/usr/local/lib/python3.12/site-packages"
VIEWS_FILE = os.path.join(SITE_PACKAGES, "projects", "views.py")


def verify_modern_architecture():
    """Verify that Bugsink has the modern dynamic form loading architecture."""
    print("Verifying Bugsink views architecture...")

    if not os.path.exists(VIEWS_FILE):
        print(f"  [ERROR] {VIEWS_FILE} does not exist!")
        return False

    with open(VIEWS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"  File size: {len(content)} bytes")

    # Check for modern architecture indicators
    checks = [
        ("get_alert_service_backend_class", "Dynamic backend class loading"),
        ("get_form_class()", "Dynamic form class loading"),
        ("get_alert_service_kind_choices", "Dynamic kind choices"),
    ]

    all_ok = True
    for pattern, description in checks:
        found = pattern in content
        status = "OK" if found else "MISSING"
        print(f"  {description}: [{status}]")
        if not found:
            all_ok = False

    if all_ok:
        print("\n  [OK] Modern architecture detected - no patching needed!")
        return True
    else:
        print("\n  [WARN] Older architecture detected - patching may be needed")
        print("  Please check if you're using Bugsink 2.0.x or later")
        return False


def main():
    print("=" * 60)
    print("Bugsink Views Patch - Architecture Verification")
    print("=" * 60)
    print()
    print("NOTE: Bugsink 2.0.12+ already has dynamic form loading.")
    print("This script now only verifies the architecture is in place.")
    print()

    if not verify_modern_architecture():
        print("\n[WARNING] Views may need manual patching for older Bugsink versions")
        print("See the original patch_views.py for the legacy patching logic")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("[SUCCESS] Views architecture verification complete!")
    print("No patching required for Bugsink 2.0.12+")
    print("=" * 60)


if __name__ == "__main__":
    main()
