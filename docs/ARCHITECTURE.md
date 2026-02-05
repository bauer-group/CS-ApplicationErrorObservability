# Architecture Decision Record: Error Tracking Platform

## Entscheidung

**Bugsink** als Error Tracking Platform anstelle von Sentry Self-Hosted.

---

## Kontext

Für internes Error Tracking und Application Observability wurde eine Self-Hosted-Lösung benötigt, die:

- Sentry-SDK-kompatibel ist (etablierte Client-Libraries)
- Ressourceneffizient betrieben werden kann
- Einfach zu deployen und zu warten ist
- Erweiterbar für eigene Integrationen (Jira, GitHub Issues, Teams, etc.)

---

## Alternativen-Bewertung

### Option 1: Sentry Self-Hosted

```
┌─────────────────────────────────────────────────────────────────┐
│                    Sentry Self-Hosted Stack                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ Sentry  │ │ Sentry  │ │ Sentry  │ │ Snuba   │ │ Relay   │   │
│  │ Web     │ │ Worker  │ │ Cron    │ │ API     │ │         │   │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │
│       │           │           │           │           │         │
│  ┌────┴───────────┴───────────┴───────────┴───────────┴────┐   │
│  │                    Message Queue                         │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐                    │   │
│  │  │ Kafka 1 │ │ Kafka 2 │ │ Kafka 3 │                    │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘                    │   │
│  │       └───────────┼───────────┘                         │   │
│  │              ┌────┴────┐                                 │   │
│  │              │Zookeeper│                                 │   │
│  │              └─────────┘                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Data Layer                            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
│  │  │PostgreSQL│ │ClickHouse│ │  Redis   │ │ Memcached│    │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Container: 20+        RAM: 8-16 GB minimum                    │
│  Startup: ~5 Minuten   Disk: 50+ GB (ClickHouse)              │
└─────────────────────────────────────────────────────────────────┘
```

**Vorteile:**
- Vollständiger Feature-Set (Performance, Profiling, Session Replay)
- Große Community
- Aktive Entwicklung

**Nachteile:**
- Extrem ressourcenintensiv (20+ Container)
- Komplexe Upgrades mit Breaking Changes
- Kafka/Zookeeper-Cluster erforderlich
- ClickHouse-Tuning notwendig
- Hoher Wartungsaufwand

---

### Option 2: Bugsink (gewählt)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Bugsink Stack                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Bugsink Server                         │   │
│  │              (Django + Snappea Workers)                  │   │
│  │                                                          │   │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐             │   │
│  │   │ HTTP API │  │ Web UI   │  │ Workers  │             │   │
│  │   │(Sentry-  │  │          │  │ (4x)     │             │   │
│  │   │compatible)│  │          │  │          │             │   │
│  │   └──────────┘  └──────────┘  └──────────┘             │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│                          │                                      │
│  ┌───────────────────────┴─────────────────────────────────┐   │
│  │                    PostgreSQL                            │   │
│  │              (Events, Projects, Users)                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Container: 2            RAM: ~1 GB                            │
│  Startup: ~10 Sekunden   Disk: Standard PostgreSQL             │
└─────────────────────────────────────────────────────────────────┘
```

**Vorteile:**
- Minimaler Ressourcenverbrauch
- Einfaches Deployment
- Sentry-SDK-kompatibel
- Gut erweiterbar (Django-basiert)
- Schnelle Upgrades

**Nachteile:**
- Weniger Features als Sentry (kein Profiling, Session Replay)
- Kleinere Community
- PolyForm Shield License (siehe [BUGSINK-LEGAL-NOTICE.md](./BUGSINK-LEGAL-NOTICE.md))

---

## Ressourcenvergleich

| Metrik | Sentry Self-Hosted | Bugsink | Faktor |
|--------|-------------------|---------|--------|
| Container | 20+ | 2 | 10x weniger |
| RAM Minimum | 8-16 GB | ~1 GB | 8-16x weniger |
| CPU (Idle) | 4+ Cores | 0.5 Cores | 8x weniger |
| Disk (Initial) | 50+ GB | 1 GB | 50x weniger |
| Startup Time | 3-5 min | 10-30 sec | 10x schneller |
| Upgrade Complexity | Hoch | Niedrig | - |

---

## Unsere Architektur

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ApplicationErrorObservability                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Anwendungen (Sentry SDKs)                                                 │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                          │
│   │ Python  │ │ Node.js │ │  .NET   │ │  Java   │  ...                     │
│   │   App   │ │   App   │ │   App   │ │   App   │                          │
│   └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘                          │
│        │           │           │           │                                │
│        └───────────┴─────┬─────┴───────────┘                                │
│                          │ HTTPS (Sentry Protocol)                          │
│                          ▼                                                  │
│   ┌──────────────────────────────────────────────────────────────────────┐ │
│   │                        Reverse Proxy (Traefik)                        │ │
│   └──────────────────────────────────────────┬───────────────────────────┘ │
│                                              │                              │
│   ┌──────────────────────────────────────────▼───────────────────────────┐ │
│   │                     Bugsink Server (Custom Build)                     │ │
│   │  ┌────────────────────────────────────────────────────────────────┐  │ │
│   │  │                    Custom Notification Backends                 │  │ │
│   │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │  │ │
│   │  │  │  Jira    │ │  GitHub  │ │  Teams   │ │ PagerDuty│ │Webhook│  │  │ │
│   │  │  │  Cloud   │ │  Issues  │ │          │ │          │ │       │  │  │ │
│   │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────┘  │  │ │
│   │  └────────────────────────────────────────────────────────────────┘  │ │
│   └──────────────────────────────────────────┬───────────────────────────┘ │
│                                              │                              │
│   ┌──────────────────────────────────────────▼───────────────────────────┐ │
│   │                           PostgreSQL 18                               │ │
│   │                    (Optimiert für SSD/NVMe)                          │ │
│   └──────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Komponenten

### 1. Bugsink Server (Custom Build)

Basierend auf dem offiziellen Bugsink-Image mit eigenen Erweiterungen:

| Komponente | Beschreibung |
|------------|--------------|
| Base Image | `bugsink/bugsink:2` |
| Workers | 4 Snappea Background Workers |
| Port | 8000 (intern) |

**Custom Notification Backends:**

| Backend | Datei | Zweck |
|---------|-------|-------|
| Jira Cloud | [jira_cloud.py](../src/backends/jira_cloud.py) | Automatische Issue-Erstellung |
| GitHub Issues | [github_issues.py](../src/backends/github_issues.py) | Issue-Tracking in GitHub |
| Microsoft Teams | [microsoft_teams.py](../src/backends/microsoft_teams.py) | Team-Benachrichtigungen |
| PagerDuty | [pagerduty.py](../src/backends/pagerduty.py) | Incident Management |
| Webhook | [webhook.py](../src/backends/webhook.py) | Generische HTTP Webhooks |

### 2. PostgreSQL

Optimierte Konfiguration für Error-Tracking-Workloads:

```
shared_buffers      = 512MB
work_mem            = 4MB
effective_cache_size = 1536MB
max_connections     = 100
```

### 3. Reverse Proxy (Optional)

Traefik-Konfiguration verfügbar in [docker-compose.traefik.yml](../docker-compose.traefik.yml).

---

## Deployment

### Minimale Anforderungen

| Ressource | Minimum | Empfohlen |
|-----------|---------|-----------|
| RAM | 2 GB | 4 GB |
| CPU | 2 Cores | 4 Cores |
| Disk | 20 GB SSD | 50 GB NVMe |

### Container-Struktur

```
docker-compose.yml
├── bugsink-server    # Application (Port 8000)
└── database-server   # PostgreSQL (Port 5432)
```

### Skalierung

Für höhere Last:
1. `SNAPPEA_NUM_WORKERS` erhöhen (default: 4)
2. PostgreSQL auf dedizierte Instanz
3. Optional: Read-Replicas für PostgreSQL

---

## SDK-Kompatibilität

Bugsink implementiert das Sentry-Protokoll. Alle offiziellen Sentry-SDKs funktionieren:

```python
# Python Beispiel
import sentry_sdk

sentry_sdk.init(
    dsn="https://key@bugsink.example.com/1",  # Bugsink statt Sentry
    traces_sample_rate=0.0,  # Performance Monitoring nicht unterstützt
)
```

Siehe [SENTRY-SDK-INTEGRATION.md](./SENTRY-SDK-INTEGRATION.md) für Details.

---

## Feature-Vergleich

| Feature | Sentry | Bugsink | Unsere Nutzung |
|---------|--------|---------|----------------|
| Error Tracking | Ja | Ja | Ja |
| Error Grouping | Ja | Ja | Ja |
| Stack Traces | Ja | Ja | Ja |
| Source Maps | Ja | Ja | Ja |
| Alerts | Ja | Ja | Ja (erweitert) |
| Issue Assignment | Ja | Ja | Ja |
| Performance Monitoring | Ja | Nein | Nicht benötigt |
| Session Replay | Ja | Nein | Nicht benötigt |
| Profiling | Ja | Nein | Nicht benötigt |

---

## Entscheidungs-Zusammenfassung

| Kriterium | Gewichtung | Sentry | Bugsink |
|-----------|------------|--------|---------|
| Ressourceneffizienz | Hoch | - | ++ |
| Wartungsaufwand | Hoch | - | ++ |
| SDK-Kompatibilität | Hoch | ++ | ++ |
| Erweiterbarkeit | Mittel | + | ++ |
| Feature-Vollständigkeit | Niedrig | ++ | + |
| **Gesamt** | | **Ausreichend** | **Gut** |

**Fazit:** Für unseren Use Case (internes Error Tracking ohne Performance Monitoring) bietet Bugsink 80% der Funktionalität bei 10% der Komplexität.

---

## Verwandte Dokumentation

- [BUGSINK-LEGAL-NOTICE.md](./BUGSINK-LEGAL-NOTICE.md) - Lizenz-Compliance
- [BUGSINK-QUICKSTART.md](./BUGSINK-QUICKSTART.md) - Schnellstart
- [BUGSINK-CONFIGURATION.md](./BUGSINK-CONFIGURATION.md) - Konfiguration
- [NOTIFICATION_BACKENDS.md](./NOTIFICATION_BACKENDS.md) - Custom Backends
- [SENTRY-SDK-INTEGRATION.md](./SENTRY-SDK-INTEGRATION.md) - SDK-Integration

---

## Dokumenthistorie

| Datum | Version | Änderung |
|-------|---------|----------|
| 2026-02-05 | 1.0 | Initial Architecture Decision Record |
