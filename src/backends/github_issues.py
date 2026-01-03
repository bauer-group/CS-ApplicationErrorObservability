"""
Bugsink Messaging Backend: GitHub Issues
=========================================

Creates issues in a GitHub repository when errors occur in Bugsink.

Compatible with Bugsink v2.

Installation:
    Copy to: /app/alerts/service_backends/github_issues.py
    The backend is automatically registered via the patch script.

Requirements:
    - GitHub repository with Issues enabled
    - Personal Access Token (classic) or Fine-grained token with 'issues:write' permission
    - Create token at: https://github.com/settings/tokens

Configuration in Bugsink UI:
    - Repository: owner/repo format, e.g., "myorg/myproject"
    - Access Token: GitHub Personal Access Token
    - Labels: Optional comma-separated labels
"""

import json
import logging
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from snappea import shared_task
from django import forms
from django.utils import timezone

logger = logging.getLogger(__name__)

# GitHub API base URL
GITHUB_API_URL = "https://api.github.com"


class GitHubIssuesConfigForm(forms.Form):
    """Configuration form for GitHub Issues integration."""

    repository = forms.CharField(
        label="Repository",
        help_text="Repository in 'owner/repo' format, e.g., 'myorg/myproject'",
        max_length=200,
        widget=forms.TextInput(attrs={"placeholder": "owner/repository"}),
    )
    access_token = forms.CharField(
        label="Access Token",
        help_text="GitHub Personal Access Token with 'repo' or 'issues:write' scope",
        widget=forms.PasswordInput(render_value=True),
    )
    labels = forms.CharField(
        label="Labels (optional)",
        help_text="Comma-separated labels to add, e.g., 'bug,bugsink,production'",
        required=False,
    )
    assignees = forms.CharField(
        label="Assignees (optional)",
        help_text="Comma-separated GitHub usernames to assign, e.g., 'user1,user2'",
        required=False,
    )

    def __init__(self, *args, config=None, **kwargs):
        """Initialize form with existing config if provided."""
        super().__init__(*args, **kwargs)
        if config:
            self.fields["repository"].initial = config.get("repository", "")
            self.fields["access_token"].initial = config.get("access_token", "")
            self.fields["labels"].initial = ",".join(config.get("labels", []))
            self.fields["assignees"].initial = ",".join(config.get("assignees", []))

    def clean_repository(self):
        """Validate repository format."""
        repo = self.cleaned_data["repository"].strip()
        if "/" not in repo or repo.count("/") != 1:
            raise forms.ValidationError("Repository must be in 'owner/repo' format")
        owner, name = repo.split("/")
        if not owner or not name:
            raise forms.ValidationError("Both owner and repository name are required")
        return repo

    def get_config(self):
        """Return configuration as dictionary for storage."""
        return {
            "repository": self.cleaned_data["repository"],
            "access_token": self.cleaned_data["access_token"],
            "labels": [l.strip() for l in self.cleaned_data.get("labels", "").split(",") if l.strip()],
            "assignees": [a.strip() for a in self.cleaned_data.get("assignees", "").split(",") if a.strip()],
        }


def _store_failure_info(service_config, error_type: str, error_message: str, response_body: str = None):
    """Store failure information for debugging."""
    service_config.last_failure_at = timezone.now()
    service_config.last_failure_info = json.dumps({
        "error_type": error_type,
        "error_message": error_message,
        "response_body": response_body[:1000] if response_body else None,
    })
    service_config.save(update_fields=["last_failure_at", "last_failure_info"])


def _store_success_info(service_config):
    """Clear failure info on success."""
    if service_config.last_failure_at is not None:
        service_config.last_failure_at = None
        service_config.last_failure_info = None
        service_config.save(update_fields=["last_failure_at", "last_failure_info"])


def _format_body(issue_id: str, state_description: str, alert_article: str,
                 alert_reason: str, **kwargs) -> str:
    """Format alert data as GitHub-flavored Markdown."""
    from issues.models import Issue

    try:
        issue = Issue.objects.select_related("project").get(pk=issue_id)

        lines = [
            "## Error Details",
            "",
            f"**Error Type:** `{issue.calculated_type or 'Unknown'}`",
            f"**Error Message:** {issue.calculated_value or 'No message'}",
            "",
            "## Timeline",
            "",
            "| First Seen | Last Seen | Event Count |",
            "|------------|-----------|-------------|",
            f"| {issue.first_seen.isoformat() if issue.first_seen else 'Unknown'} | {issue.last_seen.isoformat() if issue.last_seen else 'Unknown'} | {issue.digested_event_count} |",
            "",
            "## Context",
            "",
            f"- **Project:** {issue.project.name if issue.project else 'Unknown'}",
            f"- **Alert Type:** {state_description}",
            f"- **Reason:** {alert_reason}",
        ]

        # Add unmute reason if present
        if kwargs.get("unmute_reason"):
            lines.append(f"- **Unmute Reason:** {kwargs['unmute_reason']}")

    except Issue.DoesNotExist:
        lines = [
            "## Error Details",
            "",
            f"**Issue ID:** {issue_id}",
            f"**Alert Type:** {state_description}",
            f"**Reason:** {alert_reason}",
        ]

    lines.extend([
        "",
        "---",
        "*This issue was automatically created by [Bugsink](https://bugsink.com)*",
    ])

    return "\n".join(lines)


def _create_github_issue(config: dict, title: str, body: str) -> dict:
    """Create a GitHub issue via REST API."""
    repo = config["repository"]
    url = f"{GITHUB_API_URL}/repos/{repo}/issues"

    payload = {
        "title": title[:256],  # GitHub title recommendation
        "body": body,
    }

    # Add labels if configured
    if config.get("labels"):
        payload["labels"] = config["labels"]

    # Add assignees if configured
    if config.get("assignees"):
        payload["assignees"] = config["assignees"]

    headers = {
        "Authorization": f"Bearer {config['access_token']}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


@shared_task
def github_issues_send_test_message(config: dict, project_name: str, display_name: str,
                                     service_config_id: int):
    """Send a test issue to verify GitHub configuration."""
    from alerts.models import MessagingServiceConfig

    service_config = MessagingServiceConfig.objects.get(pk=service_config_id)

    try:
        result = _create_github_issue(
            config,
            title=f"[Bugsink] Test Issue - {project_name}",
            body=(
                "## Test Issue\n\n"
                f"This is a test issue created by **Bugsink** to verify the GitHub integration.\n\n"
                f"- **Project:** {project_name}\n"
                f"- **Service:** {display_name}\n\n"
                "If you see this issue, your configuration is working correctly.\n\n"
                "You can safely close and delete this issue.\n\n"
                "---\n"
                "*Automatically created by [Bugsink](https://bugsink.com)*"
            ),
        )

        _store_success_info(service_config)
        logger.info(f"GitHub test issue created: #{result.get('number')} - {result.get('html_url')}")

    except HTTPError as e:
        response_body = e.read().decode("utf-8") if e.fp else ""
        _store_failure_info(service_config, "HTTPError", f"Status {e.code}: {e.reason}", response_body)
        logger.error(f"GitHub API error: {e.code} - {response_body}")

    except URLError as e:
        _store_failure_info(service_config, "URLError", str(e.reason))
        logger.error(f"GitHub connection error: {e.reason}")

    except Exception as e:
        _store_failure_info(service_config, type(e).__name__, str(e))
        logger.exception(f"Unexpected error sending to GitHub: {e}")


@shared_task
def github_issues_send_alert(config: dict, issue_id: str, state_description: str,
                              alert_article: str, alert_reason: str,
                              service_config_id: int, **kwargs):
    """Create a GitHub issue for a Bugsink alert."""
    from alerts.models import MessagingServiceConfig
    from issues.models import Issue

    service_config = MessagingServiceConfig.objects.get(pk=service_config_id)

    try:
        issue = Issue.objects.select_related("project").get(pk=issue_id)
        title = f"[{state_description}] {issue.calculated_type}: {issue.calculated_value}"
    except Issue.DoesNotExist:
        title = f"[{state_description}] Issue {issue_id}"

    body = _format_body(issue_id, state_description, alert_article, alert_reason, **kwargs)

    try:
        result = _create_github_issue(
            config,
            title=title,
            body=body,
        )

        _store_success_info(service_config)
        logger.info(f"GitHub issue created for Bugsink issue {issue_id}: #{result.get('number')}")

    except HTTPError as e:
        response_body = e.read().decode("utf-8") if e.fp else ""
        _store_failure_info(service_config, "HTTPError", f"Status {e.code}: {e.reason}", response_body)
        logger.error(f"GitHub API error: {e.code} - {response_body}")

    except URLError as e:
        _store_failure_info(service_config, "URLError", str(e.reason))
        logger.error(f"GitHub connection error: {e.reason}")

    except Exception as e:
        _store_failure_info(service_config, type(e).__name__, str(e))
        logger.exception(f"Unexpected error sending to GitHub: {e}")


class GitHubIssuesBackend:
    """Backend class for GitHub Issues integration.

    Compatible with Bugsink v2 backend interface.
    """

    kind = "github_issues"
    display_name = "GitHub Issues"

    def __init__(self, service_config):
        self.service_config = service_config
        self.config = json.loads(service_config.config) if service_config.config else {}

    @classmethod
    def get_form_class(cls):
        """Return the configuration form class."""
        return GitHubIssuesConfigForm

    def send_test_message(self):
        """Queue a test message task."""
        github_issues_send_test_message.delay(
            config=self.config,
            project_name=self.service_config.project.name,
            display_name=self.service_config.display_name,
            service_config_id=self.service_config.pk,
        )

    def send_alert(self, issue_id, state_description, alert_article, alert_reason, **kwargs):
        """Queue an alert task.

        Args:
            issue_id: The Bugsink issue ID
            state_description: Description of the issue state (e.g., "New Issue", "Regression")
            alert_article: Article for the alert (e.g., "a", "an")
            alert_reason: Reason for the alert
            **kwargs: Additional arguments (e.g., unmute_reason)
        """
        github_issues_send_alert.delay(
            config=self.config,
            issue_id=str(issue_id),
            state_description=state_description,
            alert_article=alert_article,
            alert_reason=alert_reason,
            service_config_id=self.service_config.pk,
            **kwargs,
        )
