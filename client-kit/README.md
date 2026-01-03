# Client-Kit: SDK Integration Tool

Automatisiertes Tool zur Integration des Sentry SDK in deine Anwendungen.

## Features

- **Remote Installation** - Direkt aus dem Git-Repo ausführbar, kein Klonen nötig
- **Automatische Sprach-Erkennung** - Erkennt Python, Node.js, TypeScript, Java, .NET, Go, PHP, Ruby
- **Minimale, nicht-destruktive Änderungen** - Fügt nur Konfigurations-Dateien hinzu
- **Framework-Erkennung** - Erkennt Django, Flask, Express, NestJS, etc.
- **3 Modi**: Neu einrichten, DSN aktualisieren, Client-Code aktualisieren
- **Cross-Platform** - Läuft auf Windows, Linux, macOS

## Quick Start (Remote - Empfohlen)

Führe das Client-Kit direkt aus dem Repository aus - ohne es vorher zu klonen:

### Linux / macOS

```bash
# Im Projekt-Ordner ausführen
curl -sSL https://raw.githubusercontent.com/YOUR_ORG/ApplicationErrorObservability/main/client-kit/remote-install.sh | bash

# Mit DSN
curl -sSL <URL>/remote-install.sh | bash -s -- --dsn "https://key@errors.observability.app.bauer-group.com/1"

# Mit wget
wget -qO- <URL>/remote-install.sh | bash -s -- --dsn "https://..."
```

### Windows (PowerShell)

```powershell
# Im Projekt-Ordner ausführen
irm https://raw.githubusercontent.com/YOUR_ORG/ApplicationErrorObservability/main/client-kit/remote-install.ps1 | iex

# Mit DSN (erst herunterladen, dann ausführen)
Invoke-WebRequest -Uri "<URL>/remote-install.ps1" -OutFile install.ps1
.\install.ps1 -Dsn "https://key@errors.observability.app.bauer-group.com/1"
```

### Mit Umgebungsvariable für eigenes Repo

```bash
# Eigene Repo-URL setzen
export CLIENT_KIT_REPO_URL="https://raw.githubusercontent.com/DEIN_ORG/DEIN_REPO/main/client-kit"
curl -sSL $CLIENT_KIT_REPO_URL/remote-install.sh | bash
```

## Lokale Installation

Falls du das Repo bereits geklont hast:

### Option 1: Interaktiver Modus

```bash
# Linux/macOS
./install.sh

# Windows (PowerShell)
.\install.ps1

# Windows (CMD)
install.cmd
```

### Option 2: Mit Parametern

```bash
# Mit DSN
./install.sh --dsn "https://key@errors.observability.app.bauer-group.com/1"

# Nur DSN aktualisieren
./install.sh --update-dsn --dsn "https://..."

# Client-Code aktualisieren
./install.sh --update-client
```

### Option 3: Direkt mit Python

```bash
python install.py --dsn "https://key@host/1" --environment production
```

## Workflow

### 1. Projekt erstellen (manuell in Bugsink UI)

1. Öffne dein Bugsink Dashboard
2. Gehe zu **Teams** → wähle oder erstelle ein Team
3. Gehe zu **Projects** → **New Project**
4. Kopiere den **DSN** aus den Project Settings

### 2. SDK integrieren (automatisiert)

```bash
# Im Projekt-Root ausführen
cd /path/to/your/project

# Installer ausführen
/path/to/client-kit/install.sh --dsn "https://..."
```

Der Installer:
1. Erkennt die Projekt-Sprache automatisch
2. Installiert die SDK-Abhängigkeiten
3. Erstellt eine Konfigurations-Datei
4. Fügt den DSN zur `.env` hinzu

### 3. Integration abschließen

Füge den Import in deinen Entry-Point ein (wird vom Installer angezeigt):

**Python:**
```python
from sentry_config import init_sentry
init_sentry()
```

**Node.js:**
```javascript
require('./sentry.config');
```

**TypeScript:**
```typescript
import './sentry.config';
```

## Befehle

| Befehl | Beschreibung |
|--------|--------------|
| `./install.sh` | Interaktiver Modus |
| `./install.sh --dsn <DSN>` | Installation mit DSN |
| `./install.sh --update-dsn --dsn <DSN>` | Nur DSN aktualisieren |
| `./install.sh --update-client` | Client-Code aus Templates aktualisieren |
| `./install.sh --environment staging` | Environment setzen |

## Unterstützte Sprachen

| Sprache | Erkennung | SDK-Paket |
|---------|-----------|-----------|
| Python | `requirements.txt`, `pyproject.toml`, `Pipfile` | `sentry-sdk` |
| Node.js | `package.json` | `@sentry/node` |
| TypeScript | `tsconfig.json` | `@sentry/node` |
| Java | `pom.xml`, `build.gradle` | `io.sentry:sentry` |
| .NET | `*.csproj`, `*.sln` | `Sentry` |
| Go | `go.mod` | `github.com/getsentry/sentry-go` |
| PHP | `composer.json` | `sentry/sentry` |
| Ruby | `Gemfile` | `sentry-ruby` |

## Dateistruktur

Nach der Installation werden folgende Dateien erstellt:

```
your-project/
├── sentry_config.py      # Python
├── sentry.config.js      # Node.js
├── src/sentry.config.ts  # TypeScript
├── SentryConfig.java     # Java
├── SentryConfig.cs       # .NET
├── pkg/sentry/sentry.go  # Go
├── config/sentry.php     # PHP
├── config/initializers/sentry.rb  # Ruby
└── .env                  # DSN wird hier hinzugefügt
```

## Umgebungsvariablen

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `SENTRY_DSN` | Bugsink/Sentry DSN | - |
| `SENTRY_ENVIRONMENT` | Environment-Name | `production` |
| `SENTRY_TRACES_SAMPLE_RATE` | Performance Sample-Rate | `0.1` |
| `APP_VERSION` | Release-Version | - |

## Templates anpassen

Die Templates befinden sich in `templates/<language>/`. Du kannst sie anpassen:

1. Template-Datei bearbeiten
2. `./install.sh --update-client` in Projekten ausführen

### Platzhalter

| Platzhalter | Wird ersetzt durch |
|-------------|-------------------|
| `{{DSN}}` | Der konfigurierte DSN |
| `{{ENVIRONMENT}}` | Das Environment |
| `{{RELEASE}}` | Die Release-Version |

## Fehlerbehebung

### "Python not found"

Installiere Python 3.7+:
- **Windows**: https://www.python.org/downloads/
- **macOS**: `brew install python3`
- **Linux**: `apt install python3` oder `yum install python3`

### "Could not detect project language"

Stelle sicher, dass eine der erkannten Dateien im Projekt-Root existiert:
- Python: `requirements.txt`, `pyproject.toml`, `setup.py`
- Node.js: `package.json`
- etc.

### DSN wird nicht erkannt

Setze die Umgebungsvariable oder übergebe sie als Parameter:
```bash
export SENTRY_DSN="https://..."
./install.sh

# oder
./install.sh --dsn "https://..."
```

## Lizenz

Teil des Error Observability Projekts.
