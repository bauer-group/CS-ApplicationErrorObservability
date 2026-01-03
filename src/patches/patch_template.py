#!/usr/bin/env python3
"""
Template Patch for Bugsink v2
=============================

This script patches the messaging service edit template to add JavaScript
that reloads the page with the correct backend kind when the dropdown changes.
"""

import os
import sys

# Paths
SITE_PACKAGES = "/usr/local/lib/python3.12/site-packages"
TEMPLATE_FILE = os.path.join(
    SITE_PACKAGES, "projects", "templates", "projects", "project_messaging_service_edit.html"
)


def patch_template():
    """Add JavaScript to reload form when backend kind changes."""
    print("Patching messaging service template...")

    if not os.path.exists(TEMPLATE_FILE):
        print(f"  [ERROR] {TEMPLATE_FILE} does not exist!")
        return False

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"  Original file size: {len(content)} bytes")

    # Check if already patched
    if "id_kind" in content and "addEventListener" in content:
        print("  [OK] Already patched")
        return True

    original_content = content

    # Find the endblock and add JavaScript before it
    js_code = '''
<script>
document.addEventListener('DOMContentLoaded', function() {
    var kindSelect = document.getElementById('id_kind');
    if (kindSelect) {
        kindSelect.addEventListener('change', function() {
            var currentUrl = window.location.pathname;
            var newUrl = currentUrl + '?kind=' + encodeURIComponent(this.value);
            window.location.href = newUrl;
        });
    }
});
</script>

{% endblock %}'''

    if "{% endblock %}" in content:
        # Replace the last endblock with our JS + endblock
        content = content.replace("{% endblock %}", js_code, 1)
        print("  [OK] Added JavaScript for dynamic form switching")
    else:
        print("  [WARN] Could not find endblock in template")
        return False

    if content != original_content:
        with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Patched file size: {len(content)} bytes")
        print("  [OK] Template patched successfully")
        return True
    else:
        print("  [WARN] No changes made to template")
        return False


def main():
    print("=" * 60)
    print("Bugsink Template Patch - Dynamic Backend Switching")
    print("=" * 60)

    if not patch_template():
        print("\n[ERROR] Failed to patch template")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("[SUCCESS] Template patch complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
