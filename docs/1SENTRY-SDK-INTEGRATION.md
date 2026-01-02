# Sentry SDK Integration Guide

Bugsink is fully compatible with the official Sentry SDKs. This guide covers integration for popular languages and frameworks.

## DSN Format

Your Data Source Name (DSN) is the connection string that tells the SDK where to send events:

```
https://<project-key>@<hostname>/<project-id>
```

**Example:**
```
https://abc123def456@bugsink.yourcompany.com/1
```

You can find your DSN in the Bugsink project settings after creating a project.

## SDK Installation

### Python

**Installation:**
```bash
pip install sentry-sdk
```

**Basic Configuration:**
```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://your-key@bugsink.yourcompany.com/1",

    # Performance monitoring (optional)
    traces_sample_rate=0.1,  # 10% of transactions

    # Release tracking (recommended)
    release="myapp@1.0.0",

    # Environment
    environment="production",
)
```

**Django Integration:**
```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="https://your-key@bugsink.yourcompany.com/1",
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=True,  # Include user info
)
```

**Flask Integration:**
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://your-key@bugsink.yourcompany.com/1",
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.1,
)

app = Flask(__name__)
```

**FastAPI Integration:**
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

sentry_sdk.init(
    dsn="https://your-key@bugsink.yourcompany.com/1",
    integrations=[
        StarletteIntegration(),
        FastApiIntegration(),
    ],
    traces_sample_rate=0.1,
)
```

### JavaScript / Node.js

**Browser (Frontend):**
```bash
npm install @sentry/browser
```

```javascript
import * as Sentry from "@sentry/browser";

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",

    // Performance monitoring
    tracesSampleRate: 0.1,

    // Release tracking
    release: "myapp@1.0.0",

    // Environment
    environment: "production",
});
```

**Node.js (Backend):**
```bash
npm install @sentry/node
```

```javascript
const Sentry = require("@sentry/node");

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    tracesSampleRate: 0.1,
    release: "myapp@1.0.0",
    environment: "production",
});
```

**Express Integration:**
```javascript
const express = require("express");
const Sentry = require("@sentry/node");

const app = express();

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    integrations: [
        new Sentry.Integrations.Http({ tracing: true }),
        new Sentry.Integrations.Express({ app }),
    ],
    tracesSampleRate: 0.1,
});

// RequestHandler must be first middleware
app.use(Sentry.Handlers.requestHandler());
app.use(Sentry.Handlers.tracingHandler());

// Your routes here

// ErrorHandler must be before any other error middleware
app.use(Sentry.Handlers.errorHandler());
```

**React Integration:**
```bash
npm install @sentry/react
```

```jsx
import * as Sentry from "@sentry/react";

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    integrations: [
        Sentry.browserTracingIntegration(),
        Sentry.replayIntegration(),
    ],
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
});

// Wrap your app
const App = () => (
    <Sentry.ErrorBoundary fallback={<p>An error occurred</p>}>
        <YourApp />
    </Sentry.ErrorBoundary>
);
```

**Vue.js Integration:**
```bash
npm install @sentry/vue
```

```javascript
import * as Sentry from "@sentry/vue";
import { createApp } from "vue";

const app = createApp(App);

Sentry.init({
    app,
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    integrations: [
        Sentry.browserTracingIntegration(),
    ],
    tracesSampleRate: 0.1,
});

app.mount("#app");
```

### PHP

**Installation:**
```bash
composer require sentry/sentry
```

**Basic Configuration:**
```php
\Sentry\init([
    'dsn' => 'https://your-key@bugsink.yourcompany.com/1',
    'traces_sample_rate' => 0.1,
    'release' => 'myapp@1.0.0',
    'environment' => 'production',
]);
```

**Laravel Integration:**
```bash
composer require sentry/sentry-laravel
php artisan sentry:publish --dsn=https://your-key@bugsink.yourcompany.com/1
```

```php
// config/sentry.php
return [
    'dsn' => env('SENTRY_LARAVEL_DSN', 'https://your-key@bugsink.yourcompany.com/1'),
    'traces_sample_rate' => 0.1,
];
```

### Go

**Installation:**
```bash
go get github.com/getsentry/sentry-go
```

**Basic Configuration:**
```go
package main

import (
    "log"
    "github.com/getsentry/sentry-go"
)

func main() {
    err := sentry.Init(sentry.ClientOptions{
        Dsn:              "https://your-key@bugsink.yourcompany.com/1",
        TracesSampleRate: 0.1,
        Release:          "myapp@1.0.0",
        Environment:      "production",
    })
    if err != nil {
        log.Fatalf("sentry.Init: %s", err)
    }
    defer sentry.Flush(2 * time.Second)
}
```

### Ruby

**Installation:**
```bash
gem install sentry-ruby
```

**Basic Configuration:**
```ruby
require "sentry-ruby"

Sentry.init do |config|
    config.dsn = "https://your-key@bugsink.yourcompany.com/1"
    config.traces_sample_rate = 0.1
    config.release = "myapp@1.0.0"
    config.environment = "production"
end
```

**Rails Integration:**
```ruby
# Gemfile
gem "sentry-ruby"
gem "sentry-rails"

# config/initializers/sentry.rb
Sentry.init do |config|
    config.dsn = "https://your-key@bugsink.yourcompany.com/1"
    config.breadcrumbs_logger = [:active_support_logger, :http_logger]
    config.traces_sample_rate = 0.1
end
```

### .NET / C#

**Installation:**
```bash
dotnet add package Sentry
```

**Basic Configuration:**
```csharp
using Sentry;

SentrySdk.Init(options =>
{
    options.Dsn = "https://your-key@bugsink.yourcompany.com/1";
    options.TracesSampleRate = 0.1;
    options.Release = "myapp@1.0.0";
    options.Environment = "production";
});
```

**ASP.NET Core Integration:**
```csharp
// Program.cs
var builder = WebApplication.CreateBuilder(args);

builder.WebHost.UseSentry(options =>
{
    options.Dsn = "https://your-key@bugsink.yourcompany.com/1";
    options.TracesSampleRate = 0.1;
});
```

### Java

**Gradle:**
```groovy
implementation 'io.sentry:sentry:6.+'
```

**Maven:**
```xml
<dependency>
    <groupId>io.sentry</groupId>
    <artifactId>sentry</artifactId>
    <version>6.+</version>
</dependency>
```

**Configuration:**
```java
import io.sentry.Sentry;

Sentry.init(options -> {
    options.setDsn("https://your-key@bugsink.yourcompany.com/1");
    options.setTracesSampleRate(0.1);
    options.setRelease("myapp@1.0.0");
    options.setEnvironment("production");
});
```

**Spring Boot Integration:**
```yaml
# application.yml
sentry:
  dsn: https://your-key@bugsink.yourcompany.com/1
  traces-sample-rate: 0.1
```

## Common Configuration Options

### Environment

Tag events with the environment they came from:

```
environment: "production"  # or "staging", "development"
```

### Release Tracking

Track which version of your code generated an error:

```
release: "myapp@1.2.3"
```

Best practice: Set this from your build system or CI/CD pipeline.

### Sample Rate

Control what percentage of events are sent:

```
# Send all errors (recommended)
sample_rate: 1.0

# Send 10% of performance traces
traces_sample_rate: 0.1
```

### Before Send Hook

Filter or modify events before sending:

**Python:**
```python
def before_send(event, hint):
    # Don't send events from development
    if event.get("environment") == "development":
        return None
    return event

sentry_sdk.init(
    dsn="...",
    before_send=before_send,
)
```

**JavaScript:**
```javascript
Sentry.init({
    dsn: "...",
    beforeSend(event, hint) {
        // Filter out specific errors
        if (event.message?.includes("ResizeObserver")) {
            return null;
        }
        return event;
    },
});
```

### User Context

Attach user information to errors:

**Python:**
```python
from sentry_sdk import set_user

set_user({
    "id": "12345",
    "email": "user@example.com",
    "username": "johndoe",
})
```

**JavaScript:**
```javascript
Sentry.setUser({
    id: "12345",
    email: "user@example.com",
    username: "johndoe",
});
```

### Custom Tags

Add searchable metadata:

```python
sentry_sdk.set_tag("customer", "acme-corp")
sentry_sdk.set_tag("feature", "checkout")
```

### Manual Error Capture

Report errors programmatically:

**Python:**
```python
try:
    risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)
```

**JavaScript:**
```javascript
try {
    riskyOperation();
} catch (error) {
    Sentry.captureException(error);
}
```

## Testing Your Integration

### Send a Test Event

**Python:**
```python
sentry_sdk.capture_message("Hello from Bugsink!")
```

**JavaScript:**
```javascript
Sentry.captureMessage("Hello from Bugsink!");
```

### Trigger a Test Error

**Python:**
```python
try:
    1 / 0
except Exception:
    sentry_sdk.capture_exception()
```

### Verify in Bugsink

1. Log in to your Bugsink instance
2. Navigate to your project
3. Check the Issues list for your test event

## Troubleshooting

### Events Not Appearing

1. **Verify DSN:** Check for typos in your DSN
2. **Check network:** Ensure your application can reach Bugsink
   ```bash
   curl -I https://bugsink.yourcompany.com/
   ```
3. **Enable debug mode:**
   ```python
   sentry_sdk.init(dsn="...", debug=True)
   ```
4. **Check sample rate:** Ensure `sample_rate` isn't set to 0

### SSL Certificate Errors

If using self-signed certificates:

**Python:**
```python
import urllib3
urllib3.disable_warnings()

# Or configure the SDK to use custom CA
import os
os.environ["REQUESTS_CA_BUNDLE"] = "/path/to/ca-bundle.crt"
```

### Rate Limiting

If you're hitting rate limits, consider:

1. Increasing `MAX_EVENTS_PER_PROJECT_PER_HOUR` in Bugsink
2. Reducing `sample_rate` in your SDK
3. Using `before_send` to filter noisy errors

## Further Reading

- [Official Sentry Documentation](https://docs.sentry.io/)
- [Bugsink Configuration](configuration.md)
- [Bugsink Quick Start](quickstart.md)
