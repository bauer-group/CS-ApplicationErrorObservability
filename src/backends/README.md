# Bugsink Custom Messaging Backends

Custom Messaging-Backends für Bugsink v2 zur Integration mit Issue-Tracking-Systemen und Alerting-Plattformen.

**Kompatibilität:** Bugsink v2.x

## Verfügbare Backends

| Backend | Beschreibung | Datei |
|---------|--------------|-------|
| Jira Cloud | Erstellt Bug-Tickets in Jira Cloud | `jira_cloud.py` |
| GitHub Issues | Erstellt Issues in GitHub Repositories | `github_issues.py` |
| Microsoft Teams | Sendet Adaptive Cards an Teams Channels | `microsoft_teams.py` |
| PagerDuty | Erstellt Incidents für On-Call Alerting | `pagerduty.py` |
| Webhook (Generic) | Sendet JSON an beliebige HTTP Endpoints | `webhook.py` |

## Wie es funktioniert

Diese Backends werden beim Docker-Build automatisch in das Bugsink-Image integriert:

1. **COPY**: Backend-Dateien werden nach `/usr/local/lib/python3.12/site-packages/alerts/service_backends/` kopiert
2. **PATCH**: `register_backends.py` patcht `alerts/models.py` zur Registrierung
3. **CLEANUP**: Das Patch-Skript wird nach der Ausführung entfernt

### Bugsink v2 Architektur

- **Model**: `MessagingServiceConfig` mit individuellen Failure-Tracking-Feldern:
  - `last_failure_timestamp`, `last_failure_error_type`, `last_failure_error_message`
  - `last_failure_status_code`, `last_failure_response_text`, `last_failure_is_json`
  - Methode `clear_failure_status()` zum Zurücksetzen
- **Task-System**: `snappea` (nicht Celery) - Import: `from snappea.decorators import shared_task`
- **Transaktionen**: `from bugsink.transaction import immediate_atomic` für DB-Writes in Tasks
- **Backend-Registrierung**: Via `kind` choices und `get_backend()` in `alerts/models.py`
- **ConfigForm**: Verwendet `config = kwargs.pop("config", None)` Pattern
- **Config-Speicherung**: JSON im `config` TextField

## Konfiguration

### Jira Cloud

1. **API Token erstellen**: [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)

2. **In Bugsink konfigurieren**:
   - **Jira URL**: `https://your-domain.atlassian.net`
   - **User Email**: Die E-Mail, die mit dem API-Token verknüpft ist
   - **API Token**: Der erstellte Token
   - **Project Key**: z.B. `BUG`, `PROJ`
   - **Issue Type**: z.B. `Bug`, `Task`
   - **Labels**: Optional, z.B. `bugsink,production`

### GitHub Issues

1. **Personal Access Token erstellen**: [https://github.com/settings/tokens](https://github.com/settings/tokens)
   - Classic Token: `repo` Scope
   - Fine-grained Token: `issues:write` Permission

2. **In Bugsink konfigurieren**:
   - **Repository**: `owner/repository` Format, z.B. `myorg/myproject`
   - **Access Token**: Der erstellte Token
   - **Labels**: Optional, z.B. `bug,bugsink`
   - **Assignees**: Optional, z.B. `username1,username2`

### Microsoft Teams

1. **Incoming Webhook erstellen**: Channel > Connectors > Incoming Webhook

2. **In Bugsink konfigurieren**:
   - **Webhook URL**: Die generierte Webhook-URL
   - **Channel Name**: Optional, für Anzeige
   - **Mention Users**: Optional, E-Mail-Adressen für @-Mentions
   - **Theme Color**: Hex-Farbe für die Card (Standard: `d63333`)

### PagerDuty

1. **Integration erstellen**: Service > Integrations > Events API v2

2. **In Bugsink konfigurieren**:
   - **Routing Key**: 32-Zeichen Integration Key
   - **Default Severity**: `critical`, `error`, `warning`, oder `info`
   - **Service Name**: Optional, Quellname (Standard: `Bugsink`)
   - **Include Link**: Link zum Issue im Incident

### Webhook (Generic)

1. **In Bugsink konfigurieren**:
   - **Webhook URL**: HTTP(S) Endpoint
   - **HTTP Method**: `POST`, `PUT`, oder `PATCH`
   - **Secret Header**: Optional, Header-Name für Auth (z.B. `X-Webhook-Secret`)
   - **Secret Value**: Optional, Wert für den Secret Header
   - **Custom Headers**: Optional, JSON-Objekt mit zusätzlichen Headers
   - **Include Full Payload**: Vollständige Issue-Details senden

## Trigger-Events

| Event | Beschreibung |
|-------|--------------|
| `new` | Neues Issue entdeckt |
| `regression` | Bereits geschlossenes Issue tritt erneut auf |
| `unmuted` | Gemutetes Issue wurde wieder aktiviert |

## Troubleshooting

### Jira: "401 Unauthorized"

- Prüfe, ob der API-Token korrekt ist
- Stelle sicher, dass die E-Mail-Adresse mit dem Token übereinstimmt
- Verifiziere, dass der User Zugriff auf das Projekt hat

### GitHub: "404 Not Found"

- Prüfe das Repository-Format: `owner/repo`
- Stelle sicher, dass der Token `repo` oder `issues:write` Permissions hat
- Verifiziere, dass Issues im Repository aktiviert sind

### Microsoft Teams: "Bad Request"

- Prüfe, ob die Webhook-URL noch gültig ist
- Webhooks können ablaufen oder deaktiviert werden

### PagerDuty: "Invalid Routing Key"

- Der Routing Key muss exakt 32 Zeichen haben
- Stelle sicher, dass die Integration aktiv ist

### Webhook: Timeout/Connection Error

- Prüfe, ob der Endpoint erreichbar ist
- Verifiziere Firewall-Regeln und Netzwerkzugriff
