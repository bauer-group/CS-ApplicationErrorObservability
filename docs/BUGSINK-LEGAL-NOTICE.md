# Bugsink Legal Notice

## Third-Party Software Compliance

Dieses Projekt nutzt [Bugsink](https://github.com/bugsink/bugsink) als Upstream-Dependency für Error Tracking und Monitoring.

---

## Lizenzinformationen

| Komponente | Lizenz | Version |
|------------|--------|---------|
| Bugsink | PolyForm Shield License 1.0.0 | 2.0.12+ |
| Dieses Repository | MIT License | - |

---

## PolyForm Shield License 1.0.0 - Zusammenfassung

Die PolyForm Shield License ist eine **Source-Available-Lizenz**, die kommerzielle Nutzung erlaubt, jedoch mit einer **Noncompete-Klausel**.

### Erlaubte Nutzung

Die Lizenz erlaubt ausdrücklich:

> *"Any purpose is a permitted purpose, except for providing any product that competes with the software..."*

### Änderungen und Patches

> *"The licensor grants you an additional copyright license to make changes and new works based on the software for any permitted purpose."*

Eigene Patches und Anpassungen sind für erlaubte Zwecke gestattet.

---

## Unsere Nutzung - Compliance-Erklärung

### Erlaubter Nutzungszweck

Wir nutzen Bugsink **ausschließlich für**:

- Internes Bugtracking der eigenen Software
- Development und Debugging
- Internes Monitoring und Observability
- Fehleranalyse im Entwicklungsprozess

### Bestätigung der Lizenzkonformität

| Kriterium | Status | Erläuterung |
|-----------|--------|-------------|
| Nur interne Nutzung | Ja | Kein externer Zugriff durch Dritte |
| Nur eigene Software | Ja | Bugtracking nur für eigene Anwendungen |
| Kein Kundenzugriff | Ja | Keine Bereitstellung für Endkunden |
| Keine Vermarktung | Ja | Kein kommerzielles Angebot |
| Kein Hosted/Managed Service | Ja | Keine SaaS-Bereitstellung |
| Kein konkurrierendes Produkt | Ja | Wir bieten kein Bugtracking-Produkt an |

**Ergebnis: Lizenzkonform nach PolyForm Shield License 1.0.0**

---

## Verbotene Nutzungsszenarien

Die folgenden Nutzungen sind **nicht gestattet** und würden einen Lizenzverstoß darstellen:

### Absolute Verbote

1. **Bereitstellung als Service**
   - Bugsink als SaaS/PaaS für Dritte anbieten
   - Hosted Bugtracking für externe Kunden
   - Managed Error Tracking Service

2. **Konkurrenzprodukt**
   - Ein Produkt entwickeln/vertreiben, das mit Bugsink konkurriert
   - Bugsink als Feature eines verkauften Produkts einbinden
   - White-Label Error Tracking

3. **Externe Bereitstellung**
   - Kundenzugriff auf die Bugsink-Instanz
   - Partner-Zugriff ohne separate Lizenzvereinbarung
   - Öffentlicher Zugang

> *"Goods and services compete even when provided free of charge."*
> — PolyForm Shield License 1.0.0, Section: Competition

---

## Red-Line Checkliste

Vor jeder Erweiterung der Nutzung diese Fragen prüfen:

| Frage | Wenn "Ja" → Aktion erforderlich |
|-------|--------------------------------|
| Werden Externe (Kunden, Partner) Zugriff auf Bugsink erhalten? | Lizenzprüfung / Alternative suchen |
| Wird Bugsink Teil eines verkauften Produkts? | Lizenzprüfung / Alternative suchen |
| Wird ein Service angeboten, der auf Bugsink basiert? | Lizenzprüfung / Alternative suchen |
| Könnte unsere Nutzung als "konkurrierendes Produkt" gesehen werden? | Lizenzprüfung / Alternative suchen |

---

## Angewandte Patches

Dieses Repository enthält eigene Patches für Bugsink, die gemäß der "Changes and New Works License" erlaubt sind:

| Patch | Zweck | Dateien |
|-------|-------|---------|
| Notification Backends | Erweiterte Benachrichtigungsoptionen | Siehe [NOTIFICATION_BACKENDS.md](./NOTIFICATION_BACKENDS.md) |

Alle Patches dienen ausschließlich der internen Nutzung für eigenes Bugtracking.

---

## Exit-Strategie

Sollte sich unser Nutzungsszenario ändern und die Lizenzkonformität gefährdet sein:

### Optionen

1. **Kommerzielle Lizenz**
   - Kontakt: Bugsink-Maintainer für kommerzielle Lizenzierung

2. **Alternative Lösungen**
   - Sentry (Self-Hosted, BSD-3-Clause)
   - GlitchTip (MIT License)
   - Andere Open-Source Error Tracker

3. **Eigenentwicklung**
   - Basierend auf diesem Repository ohne Bugsink-Abhängigkeit

---

## Verantwortlichkeiten

| Rolle | Verantwortung |
|-------|---------------|
| Development Team | Einhaltung der Nutzungseinschränkungen |
| Tech Lead | Review bei Änderungen am Nutzungsszenario |
| Legal / Compliance | Jährliche Überprüfung der Lizenzkonformität |

---

## Lizenztext-Referenz

Der vollständige Lizenztext der PolyForm Shield License 1.0.0 ist verfügbar unter:
- https://polyformproject.org/licenses/shield/1.0.0

---

## Dokumenthistorie

| Datum | Version | Änderung |
|-------|---------|----------|
| 2026-02-05 | 1.0 | Initiale Legal Notice erstellt |

---

## Zusammenfassung

> **Die interne Nutzung von Bugsink ausschließlich für eigenes Bugtracking, internes Development und Monitoring ohne externe Bereitstellung ist nach der PolyForm Shield License 1.0.0 zulässig.**

Bei Fragen zur Lizenzkonformität: Legal/Compliance konsultieren **bevor** Änderungen am Nutzungsszenario vorgenommen werden.
