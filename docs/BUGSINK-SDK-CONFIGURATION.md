# Bugsink-Specific SDK Configuration

Bugsink is compatible with the Sentry SDK, but since it's self-hosted, there are important configuration differences compared to Sentry's SaaS offering.

> **Note:** If you configured your SDK using the Bugsink UI, these settings are already applied. This guide is primarily for users migrating from Sentry or configuring manually.

## Key Differences from Sentry

| Setting | Sentry (SaaS) | Bugsink (Self-Hosted) | Reason |
|---------|---------------|----------------------|--------|
| `send_default_pii` | `false` | `true` | Your data stays on your servers |
| `traces_sample_rate` | `0.1` | `0` | Bugsink doesn't support traces |
| Max local variables | 10 | Adjustable | Self-hosted allows larger payloads |

---

## Recommended Configuration

### Python

```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://your-key@bugsink.yourcompany.com/1",

    # BUGSINK-SPECIFIC: Enable PII since data stays on your servers
    send_default_pii=True,

    # BUGSINK-SPECIFIC: Disable traces (not supported)
    traces_sample_rate=0,

    # Standard settings
    environment="production",
    release="myapp@1.2.3",
    sample_rate=1.0,
    max_breadcrumbs=100,
    attach_stacktrace=True,
)
```

### JavaScript / Node.js

```javascript
import * as Sentry from "@sentry/node";  // or @sentry/browser

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",

    // BUGSINK-SPECIFIC: Enable PII since data stays on your servers
    sendDefaultPii: true,

    // BUGSINK-SPECIFIC: Disable traces (not supported)
    tracesSampleRate: 0,

    // Standard settings
    environment: "production",
    release: "myapp@1.2.3",
    sampleRate: 1.0,
});
```

### PHP

```php
\Sentry\init([
    'dsn' => 'https://your-key@bugsink.yourcompany.com/1',

    // BUGSINK-SPECIFIC: Enable PII since data stays on your servers
    'send_default_pii' => true,

    // BUGSINK-SPECIFIC: Disable traces (not supported)
    'traces_sample_rate' => 0,

    // Standard settings
    'environment' => 'production',
    'release' => 'myapp@1.2.3',
]);
```

### Go

```go
import "github.com/getsentry/sentry-go"

sentry.Init(sentry.ClientOptions{
    Dsn: "https://your-key@bugsink.yourcompany.com/1",

    // BUGSINK-SPECIFIC: Disable traces (not supported)
    TracesSampleRate: 0,

    // Standard settings
    Environment: "production",
    Release:     "myapp@1.2.3",
})
```

### Ruby

```ruby
Sentry.init do |config|
    config.dsn = "https://your-key@bugsink.yourcompany.com/1"

    # BUGSINK-SPECIFIC: Enable PII since data stays on your servers
    config.send_default_pii = true

    # BUGSINK-SPECIFIC: Disable traces (not supported)
    config.traces_sample_rate = 0

    # Standard settings
    config.environment = "production"
    config.release = "myapp@1.2.3"
end
```

### Java / Kotlin

```java
import io.sentry.Sentry;

Sentry.init(options -> {
    options.setDsn("https://your-key@bugsink.yourcompany.com/1");

    // BUGSINK-SPECIFIC: Enable PII since data stays on your servers
    options.setSendDefaultPii(true);

    // BUGSINK-SPECIFIC: Disable traces (not supported)
    options.setTracesSampleRate(0.0);

    // Standard settings
    options.setEnvironment("production");
    options.setRelease("myapp@1.2.3");
});
```

### .NET / C#

```csharp
using Sentry;

SentrySdk.Init(options =>
{
    options.Dsn = "https://your-key@bugsink.yourcompany.com/1";

    // BUGSINK-SPECIFIC: Enable PII since data stays on your servers
    options.SendDefaultPii = true;

    // BUGSINK-SPECIFIC: Disable traces (not supported)
    options.TracesSampleRate = 0;

    // Standard settings
    options.Environment = "production";
    options.Release = "myapp@1.2.3";
});
```

---

## PII Configuration Details

### What PII Gets Sent

When `send_default_pii=True`, the SDK includes:

| Data Type | Examples |
|-----------|----------|
| User IP address | Automatically captured from requests |
| User cookies | Session cookies, auth tokens |
| HTTP headers | Authorization, User-Agent, etc. |
| Request body | Form data, JSON payloads |
| User data | If explicitly set via `set_user()` |

### Why Enable PII for Bugsink

**Sentry (SaaS):**
- Data is sent to third-party servers
- Privacy regulations (GDPR, CCPA) apply
- Default: `send_default_pii=False`

**Bugsink (Self-Hosted):**
- Data stays on **your** infrastructure
- You control data retention and access
- More debugging information = faster resolution
- Recommended: `send_default_pii=True`

### Selective PII Control

If you want PII but need to filter specific sensitive data:

```python
import sentry_sdk

def before_send(event, hint):
    # Remove specific sensitive headers
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        sensitive_headers = ["Authorization", "X-API-Key", "Cookie"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[Filtered]"

    # Remove credit card numbers from request body
    if "request" in event and "data" in event["request"]:
        data = event["request"]["data"]
        if isinstance(data, dict) and "card_number" in data:
            data["card_number"] = "[Filtered]"

    return event

sentry_sdk.init(
    dsn="...",
    send_default_pii=True,  # Enable PII
    before_send=before_send,  # But filter sensitive fields
)
```

---

## Traces Configuration

### Why Traces Are Disabled

Bugsink intentionally does not support performance monitoring/traces because:

1. **Focus:** Bugsink focuses on error tracking, not APM
2. **Simplicity:** Reduces complexity and resource usage
3. **Storage:** Traces generate significant data volume

### Verifying Traces Are Disabled

Ensure your configuration includes:

```python
# Python
traces_sample_rate=0

# JavaScript
tracesSampleRate: 0

# Other SDKs
traces_sample_rate: 0
```

### If You Need Performance Monitoring

Consider dedicated APM tools:
- OpenTelemetry
- Jaeger
- Datadog APM
- New Relic

These can run alongside Bugsink without conflict.

---

## Python: Preserving Local Variables

By default, the Python SDK limits local variables to **10 per frame**. For complex debugging, you may want more.

### The Problem

```python
def process_order(order_id, customer, items, shipping, billing, discount, tax, total, currency, notes, metadata):
    # Only first 10 variables are captured!
    raise ValueError("Something went wrong")
```

### Solution: Monkey Patching

Add this **before** `sentry_sdk.init()`:

```python
import sentry_sdk.utils

# Increase max local variables per frame (default is 10)
sentry_sdk.utils.MAX_STRING_LENGTH = 2048  # Max string length
sentry_sdk.utils.MAX_FORMAT_PARAM_LENGTH = 1024

# Patch to capture more local variables
original_get_locals = sentry_sdk.utils.get_locals

def patched_get_locals(frame):
    """Capture all local variables, not just the first 10."""
    return {
        key: value
        for key, value in frame.f_locals.items()
    }

sentry_sdk.utils.get_locals = patched_get_locals

# Now initialize Sentry
sentry_sdk.init(
    dsn="...",
    send_default_pii=True,
)
```

### Server-Side Configuration

Large payloads may be rejected by default. Adjust Bugsink's limits:

```ini
# .env
MAX_EVENT_SIZE=10485760        # 10 MB (default: 1 MB)
MAX_ENVELOPE_SIZE=104857600    # 100 MB
```

### Warning

Capturing all local variables can:
- Significantly increase event size
- Include sensitive data accidentally
- Impact application performance

Use selectively in development/staging environments.

---

## Framework-Specific Examples

### Django

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="https://your-key@bugsink.yourcompany.com/1",

    # BUGSINK-SPECIFIC
    send_default_pii=True,
    traces_sample_rate=0,

    integrations=[
        DjangoIntegration(
            transaction_style="url",
            middleware_spans=False,  # No traces
            signals_spans=False,     # No traces
            cache_spans=False,       # No traces
        ),
    ],

    # Include request data
    request_bodies="always",  # or "medium", "small", "never"
)
```

### Flask

```python
from flask import Flask
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://your-key@bugsink.yourcompany.com/1",

    # BUGSINK-SPECIFIC
    send_default_pii=True,
    traces_sample_rate=0,

    integrations=[
        FlaskIntegration(
            transaction_style="url",
        ),
    ],
)

app = Flask(__name__)
```

### FastAPI

```python
from fastapi import FastAPI
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

sentry_sdk.init(
    dsn="https://your-key@bugsink.yourcompany.com/1",

    # BUGSINK-SPECIFIC
    send_default_pii=True,
    traces_sample_rate=0,

    integrations=[
        StarletteIntegration(transaction_style="endpoint"),
        FastApiIntegration(transaction_style="endpoint"),
    ],
)

app = FastAPI()
```

### Express.js

```javascript
const express = require("express");
const Sentry = require("@sentry/node");

const app = express();

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",

    // BUGSINK-SPECIFIC
    sendDefaultPii: true,
    tracesSampleRate: 0,

    integrations: [
        // Only error tracking, no tracing integration
        new Sentry.Integrations.Http({ tracing: false }),
    ],
});

// Only use request handler, not tracing handler
app.use(Sentry.Handlers.requestHandler({
    user: true,
    ip: true,
    request: true,
}));

// Your routes...

app.use(Sentry.Handlers.errorHandler());
```

### Laravel

```php
// config/sentry.php
return [
    'dsn' => env('SENTRY_LARAVEL_DSN'),

    // BUGSINK-SPECIFIC
    'send_default_pii' => true,
    'traces_sample_rate' => 0,

    // Standard settings
    'environment' => env('APP_ENV', 'production'),
    'release' => env('SENTRY_RELEASE'),
];
```

### Rails

```ruby
# config/initializers/sentry.rb
Sentry.init do |config|
    config.dsn = ENV["SENTRY_DSN"]

    # BUGSINK-SPECIFIC
    config.send_default_pii = true
    config.traces_sample_rate = 0

    # Standard settings
    config.environment = Rails.env
    config.release = MyApp::VERSION

    # Include request data
    config.breadcrumbs_logger = [:active_support_logger, :http_logger]
end
```

---

## Migration Checklist: Sentry → Bugsink

When migrating from Sentry to Bugsink:

- [ ] Update DSN to point to your Bugsink instance
- [ ] Set `send_default_pii=True`
- [ ] Set `traces_sample_rate=0`
- [ ] Remove any tracing integrations (optional, but saves resources)
- [ ] Consider increasing `MAX_EVENT_SIZE` in Bugsink if needed
- [ ] Test with a sample error: `sentry_sdk.capture_message("Test")`

---

## Summary

| Configuration | Sentry Default | Bugsink Recommended |
|--------------|----------------|---------------------|
| `send_default_pii` | `False` | `True` |
| `traces_sample_rate` | `0.1` | `0` |
| `sample_rate` | `1.0` | `1.0` |
| `attach_stacktrace` | `True` | `True` |
| `max_breadcrumbs` | `100` | `100` |

The key insight: **Bugsink is self-hosted, so you control your data.** Enable all debugging information you need without privacy concerns about third-party data sharing.

---

## Further Reading

- [Configuration Reference](CONFIGURATION.md)
- [Quick Start Guide](QUICKSTART.md)
- [Complete SDK Reference](SENTRY-SDK-COMPLETE-REFERENCE.md)
