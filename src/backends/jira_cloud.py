"""
Bugsink Messaging Backend: Jira Cloud
======================================

Creates bug tickets in Jira Cloud when issues occur in Bugsink.

Compatible with Bugsink v2.

Installation:
    Copy to: /app/alerts/service_backends/jira_cloud.py
    The backend is automatically registered via the patch script.

Requirements:
    - Jira Cloud instance with API access
    - API Token (create at: https://id.atlassian.com/manage-profile/security/api-tokens)
    - User email associated with the API token

Configuration in Bugsink UI:
    - Jira URL: https://your-domain.atlassian.net
    - User Email: your-email@example.com
    - API Token: your-api-token
    - Project Key: e.g., "BUG" or "PROJ"
    - Issue Type: e.g., "Bug", "Task"
"""

import json
import logging
from base64 import b64encode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from snappea import shared_task
from django import forms
from django.utils import timezone

logger = logging.getLogger(__name__)


# Standard Jira Issue Types (Cloud)
JIRA_ISSUE_TYPE_CHOICES = [
    ("Bug", "Bug"),
    ("Task", "Task"),
    ("Story", "Story"),
    ("Epic", "Epic"),
    ("Sub-task", "Sub-task"),
    ("Improvement", "Improvement"),
    ("New Feature", "New Feature"),
]


class JiraCloudConfigForm(forms.Form):
    """Configuration form for Jira Cloud integration."""

    jira_url = forms.URLField(
        label="Jira URL",
        help_text="Your Jira Cloud URL, e.g., https://your-domain.atlassian.net",
        widget=forms.URLInput(attrs={"placeholder": "https://your-domain.atlassian.net"}),
    )
    user_email = forms.EmailField(
        label="User Email",
        help_text="Email address associated with the API token",
    )
    api_token = forms.CharField(
        label="API Token",
        help_text="Jira API token (create at id.atlassian.com)",
        widget=forms.PasswordInput(render_value=True),
    )
    project_key = forms.CharField(
        label="Project Key",
        help_text="Jira project key, e.g., 'BUG' or 'PROJ'",
        max_length=20,
        initial="PROJ",
    )
    issue_type = forms.ChoiceField(
        label="Issue Type",
        help_text="Type of issue to create",
        choices=JIRA_ISSUE_TYPE_CHOICES,
        initial="Bug",
    )
    labels = forms.CharField(
        label="Labels (optional)",
        help_text="Comma-separated labels to add, e.g., 'bugsink,production'",
        initial="error-observer",
        required=False,
    )

    def __init__(self, *args, config=None, **kwargs):
        """Initialize form with existing config if provided."""
        super().__init__(*args, **kwargs)
        if config:
            self.fields["jira_url"].initial = config.get("jira_url", "")
            self.fields["user_email"].initial = config.get("user_email", "")
            self.fields["api_token"].initial = config.get("api_token", "")
            self.fields["project_key"].initial = config.get("project_key", "")
            self.fields["issue_type"].initial = config.get("issue_type", "Bug")
            self.fields["labels"].initial = ",".join(config.get("labels", []))

    def get_config(self):
        """Return configuration as dictionary for storage."""
        return {
            "jira_url": self.cleaned_data["jira_url"].rstrip("/"),
            "user_email": self.cleaned_data["user_email"],
            "api_token": self.cleaned_data["api_token"],
            "project_key": self.cleaned_data["project_key"],
            "issue_type": self.cleaned_data["issue_type"],
            "labels": [l.strip() for l in self.cleaned_data.get("labels", "").split(",") if l.strip()],
        }


def _get_auth_header(email: str, api_token: str) -> str:
    """Create Basic Auth header for Jira API."""
    credentials = f"{email}:{api_token}"
    encoded = b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


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


def _format_description(issue_id: str, state_description: str, alert_article: str,
                        alert_reason: str, **kwargs) -> str:
    """Format alert data as Jira description."""
    from issues.models import Issue

    try:
        issue = Issue.objects.select_related("project").get(pk=issue_id)

        lines = [
            f"*Error Type:* {issue.calculated_type or 'Unknown'}",
            f"*Error Message:* {issue.calculated_value or 'No message'}",
            "",
            f"*First Seen:* {issue.first_seen.isoformat() if issue.first_seen else 'Unknown'}",
            f"*Last Seen:* {issue.last_seen.isoformat() if issue.last_seen else 'Unknown'}",
            f"*Event Count:* {issue.digested_event_count}",
            "",
            f"*Project:* {issue.project.name if issue.project else 'Unknown'}",
            "",
            f"*Alert Type:* {state_description}",
            f"*Reason:* {alert_reason}",
        ]

        # Add unmute reason if present
        if kwargs.get("unmute_reason"):
            lines.append(f"*Unmute Reason:* {kwargs['unmute_reason']}")

    except Issue.DoesNotExist:
        lines = [
            f"*Issue ID:* {issue_id}",
            f"*Alert Type:* {state_description}",
            f"*Reason:* {alert_reason}",
        ]

    return "\n".join(lines)


def _create_jira_issue(config: dict, summary: str, description: str) -> dict:
    """Create a Jira issue via REST API."""
    url = f"{config['jira_url']}/rest/api/3/issue"

    payload = {
        "fields": {
            "project": {"key": config["project_key"]},
            "summary": summary[:255],  # Jira summary limit
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}]
                    }
                ]
            },
            "issuetype": {"name": config["issue_type"]},
        }
    }

    # Add labels if configured
    if config.get("labels"):
        payload["fields"]["labels"] = config["labels"]

    headers = {
        "Authorization": _get_auth_header(config["user_email"], config["api_token"]),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


@shared_task
def jira_cloud_send_test_message(config: dict, project_name: str, display_name: str,
                                  service_config_id: int):
    """Send a test message to verify Jira configuration."""
    from alerts.models import MessagingServiceConfig

    service_config = MessagingServiceConfig.objects.get(pk=service_config_id)

    try:
        result = _create_jira_issue(
            config,
            summary=f"[Bugsink] Test Issue - {project_name}",
            description=(
                f"This is a test issue created by Bugsink to verify the Jira integration.\n\n"
                f"Project: {project_name}\n"
                f"Service: {display_name}\n\n"
                "If you see this issue, your configuration is working correctly.\n\n"
                "You can safely delete this issue."
            ),
        )

        _store_success_info(service_config)
        logger.info(f"Jira test issue created: {result.get('key')}")

    except HTTPError as e:
        response_body = e.read().decode("utf-8") if e.fp else ""
        _store_failure_info(service_config, "HTTPError", f"Status {e.code}: {e.reason}", response_body)
        logger.error(f"Jira API error: {e.code} - {response_body}")

    except URLError as e:
        _store_failure_info(service_config, "URLError", str(e.reason))
        logger.error(f"Jira connection error: {e.reason}")

    except Exception as e:
        _store_failure_info(service_config, type(e).__name__, str(e))
        logger.exception(f"Unexpected error sending to Jira: {e}")


@shared_task
def jira_cloud_send_alert(config: dict, issue_id: str, state_description: str,
                          alert_article: str, alert_reason: str,
                          service_config_id: int, **kwargs):
    """Create a Jira issue for a Bugsink alert."""
    from alerts.models import MessagingServiceConfig
    from issues.models import Issue

    service_config = MessagingServiceConfig.objects.get(pk=service_config_id)

    try:
        issue = Issue.objects.select_related("project").get(pk=issue_id)
        summary = f"[{state_description}] {issue.calculated_type}: {issue.calculated_value}"
    except Issue.DoesNotExist:
        summary = f"[{state_description}] Issue {issue_id}"

    description = _format_description(issue_id, state_description, alert_article,
                                       alert_reason, **kwargs)

    try:
        result = _create_jira_issue(
            config,
            summary=summary,
            description=description,
        )

        _store_success_info(service_config)
        logger.info(f"Jira issue created for Bugsink issue {issue_id}: {result.get('key')}")

    except HTTPError as e:
        response_body = e.read().decode("utf-8") if e.fp else ""
        _store_failure_info(service_config, "HTTPError", f"Status {e.code}: {e.reason}", response_body)
        logger.error(f"Jira API error: {e.code} - {response_body}")

    except URLError as e:
        _store_failure_info(service_config, "URLError", str(e.reason))
        logger.error(f"Jira connection error: {e.reason}")

    except Exception as e:
        _store_failure_info(service_config, type(e).__name__, str(e))
        logger.exception(f"Unexpected error sending to Jira: {e}")


class JiraCloudBackend:
    """Backend class for Jira Cloud integration.

    Compatible with Bugsink v2 backend interface.
    """

    kind = "jira_cloud"
    display_name = "Jira Cloud"

    def __init__(self, service_config):
        self.service_config = service_config
        self.config = json.loads(service_config.config) if service_config.config else {}

    @classmethod
    def get_form_class(cls):
        """Return the configuration form class."""
        return JiraCloudConfigForm

    def send_test_message(self):
        """Queue a test message task."""
        jira_cloud_send_test_message.delay(
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
        jira_cloud_send_alert.delay(
            config=self.config,
            issue_id=str(issue_id),
            state_description=state_description,
            alert_article=alert_article,
            alert_reason=alert_reason,
            service_config_id=self.service_config.pk,
            **kwargs,
        )
