#!/usr/bin/env python3
"""
Views Patch for Bugsink v2
==========================

This script patches projects/views.py to dynamically load the correct
ConfigForm based on the selected backend kind.

The original code hardcodes SlackConfigForm, which prevents other backends
from showing their specific configuration fields.
"""

import os
import sys
import re

# Paths
SITE_PACKAGES = "/usr/local/lib/python3.12/site-packages"
VIEWS_FILE = os.path.join(SITE_PACKAGES, "projects", "views.py")


def patch_views_file():
    """Patch projects/views.py to use dynamic ConfigForm loading."""
    print("Patching projects/views.py for dynamic backend forms...")

    if not os.path.exists(VIEWS_FILE):
        print(f"  [ERROR] {VIEWS_FILE} does not exist!")
        return False

    with open(VIEWS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"  Original file size: {len(content)} bytes")

    # Check if already patched
    if "get_config_form_for_kind" in content:
        print("  [OK] Already patched")
        return True

    original_content = content

    # === STEP 1: Update imports ===
    # Find the SlackConfigForm import and replace it with our helper function
    old_import = "from alerts.service_backends.slack import SlackConfigForm"
    new_import = """from alerts.service_backends.slack import SlackConfigForm

# Dynamic ConfigForm loader for multiple backends
def get_config_form_for_kind(kind):
    \"\"\"Return the appropriate ConfigForm class for the given backend kind.\"\"\"
    if kind == "slack":
        return SlackConfigForm
    elif kind == "jira_cloud":
        from alerts.service_backends.jira_cloud import JiraCloudConfigForm
        return JiraCloudConfigForm
    elif kind == "github_issues":
        from alerts.service_backends.github_issues import GitHubIssuesConfigForm
        return GitHubIssuesConfigForm
    elif kind == "microsoft_teams":
        from alerts.service_backends.microsoft_teams import MicrosoftTeamsConfigForm
        return MicrosoftTeamsConfigForm
    elif kind == "pagerduty":
        from alerts.service_backends.pagerduty import PagerDutyConfigForm
        return PagerDutyConfigForm
    elif kind == "webhook":
        from alerts.service_backends.webhook import WebhookConfigForm
        return WebhookConfigForm
    else:
        # Default to Slack for unknown kinds
        return SlackConfigForm"""

    if old_import in content:
        content = content.replace(old_import, new_import)
        print("  [OK] Added get_config_form_for_kind helper function")
    else:
        print("  [WARN] Could not find SlackConfigForm import")
        return False

    # === STEP 2: Patch project_messaging_service_add ===
    # Replace the hardcoded SlackConfigForm with dynamic form loading
    old_add_view = '''@atomic_for_request_method
def project_messaging_service_add(request, project_pk):
    project = Project.objects.get(id=project_pk, is_deleted=False)
    _check_project_admin(project, request.user)

    if request.method == 'POST':
        form = MessagingServiceConfigForm(project, request.POST)
        config_form = SlackConfigForm(data=request.POST)

        if form.is_valid() and config_form.is_valid():
            service = form.save(commit=False)
            service.config = json.dumps(config_form.get_config())
            service.save()

            messages.success(request, "Messaging service added successfully.")
            return redirect('project_alerts_setup', project_pk=project_pk)

    else:
        form = MessagingServiceConfigForm(project)
        config_form = SlackConfigForm()

    return render(request, 'projects/project_messaging_service_edit.html', {
        'project': project,
        'form': form,
        'config_form': config_form,
    })'''

    new_add_view = '''@atomic_for_request_method
def project_messaging_service_add(request, project_pk):
    project = Project.objects.get(id=project_pk, is_deleted=False)
    _check_project_admin(project, request.user)

    if request.method == 'POST':
        form = MessagingServiceConfigForm(project, request.POST)
        kind = request.POST.get('kind', 'slack')
        ConfigFormClass = get_config_form_for_kind(kind)
        config_form = ConfigFormClass(data=request.POST)

        if form.is_valid() and config_form.is_valid():
            service = form.save(commit=False)
            service.config = json.dumps(config_form.get_config())
            service.save()

            messages.success(request, "Messaging service added successfully.")
            return redirect('project_alerts_setup', project_pk=project_pk)

    else:
        kind = request.GET.get('kind', 'slack')
        form = MessagingServiceConfigForm(project, initial={'kind': kind})
        ConfigFormClass = get_config_form_for_kind(kind)
        config_form = ConfigFormClass()

    return render(request, 'projects/project_messaging_service_edit.html', {
        'project': project,
        'form': form,
        'config_form': config_form,
    })'''

    if old_add_view in content:
        content = content.replace(old_add_view, new_add_view)
        print("  [OK] Patched project_messaging_service_add view")
    else:
        print("  [WARN] Could not find project_messaging_service_add view pattern")

    # === STEP 3: Patch project_messaging_service_edit ===
    old_edit_view = '''@atomic_for_request_method
def project_messaging_service_edit(request, project_pk, service_pk):
    project = Project.objects.get(id=project_pk, is_deleted=False)
    _check_project_admin(project, request.user)

    instance = project.service_configs.get(id=service_pk)

    if request.method == 'POST':
        form = MessagingServiceConfigForm(project, request.POST, instance=instance)
        config_form = SlackConfigForm(data=request.POST)

        if form.is_valid() and config_form.is_valid():
            service = form.save(commit=False)
            service.config = json.dumps(config_form.get_config())
            service.save()

            messages.success(request, "Messaging service updated successfully.")
            return redirect('project_alerts_setup', project_pk=project_pk)

    else:
        form = MessagingServiceConfigForm(project, instance=instance)
        config_form = SlackConfigForm(config=json.loads(instance.config))

    return render(request, 'projects/project_messaging_service_edit.html', {
        'project': project,
        'service_config': instance,
        'form': form,
        'config_form': config_form,
    })'''

    new_edit_view = '''@atomic_for_request_method
def project_messaging_service_edit(request, project_pk, service_pk):
    project = Project.objects.get(id=project_pk, is_deleted=False)
    _check_project_admin(project, request.user)

    instance = project.service_configs.get(id=service_pk)
    ConfigFormClass = get_config_form_for_kind(instance.kind)

    if request.method == 'POST':
        form = MessagingServiceConfigForm(project, request.POST, instance=instance)
        kind = request.POST.get('kind', instance.kind)
        ConfigFormClass = get_config_form_for_kind(kind)
        config_form = ConfigFormClass(data=request.POST)

        if form.is_valid() and config_form.is_valid():
            service = form.save(commit=False)
            service.config = json.dumps(config_form.get_config())
            service.save()

            messages.success(request, "Messaging service updated successfully.")
            return redirect('project_alerts_setup', project_pk=project_pk)

    else:
        form = MessagingServiceConfigForm(project, instance=instance)
        config_form = ConfigFormClass(config=json.loads(instance.config))

    return render(request, 'projects/project_messaging_service_edit.html', {
        'project': project,
        'service_config': instance,
        'form': form,
        'config_form': config_form,
    })'''

    if old_edit_view in content:
        content = content.replace(old_edit_view, new_edit_view)
        print("  [OK] Patched project_messaging_service_edit view")
    else:
        print("  [WARN] Could not find project_messaging_service_edit view pattern")

    # Write the patched content
    if content != original_content:
        with open(VIEWS_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Patched file size: {len(content)} bytes")
        print("  [OK] views.py patched successfully")
        return True
    else:
        print("  [WARN] No changes made to views.py")
        return False


def verify_syntax():
    """Verify the patched file has valid Python syntax."""
    print("\nVerifying Python syntax...")

    try:
        with open(VIEWS_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        compile(content, VIEWS_FILE, "exec")
        print("  [OK] Syntax is valid")
        return True

    except SyntaxError as e:
        print(f"  [ERROR] Syntax error: {e}")
        print(f"  Line {e.lineno}: {e.text}")
        return False


def main():
    print("=" * 60)
    print("Bugsink Views Patch - Dynamic ConfigForm Loading")
    print("=" * 60)

    if not patch_views_file():
        print("\n[ERROR] Failed to patch views.py")
        sys.exit(1)

    if not verify_syntax():
        print("\n[ERROR] Patched file has syntax errors")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("[SUCCESS] Views patch complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
