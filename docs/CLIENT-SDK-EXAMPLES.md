# Client SDK Integration Examples

This document provides comprehensive integration guides for connecting your applications to the Error Observability platform using the Sentry SDK.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Supported Languages](#supported-languages)
- [DSN Configuration](#dsn-configuration)
- [Common Features](#common-features)
- [Language-Specific Guides](#language-specific-guides)
  - [Python](#python)
  - [JavaScript / Node.js](#javascript--nodejs)
  - [TypeScript](#typescript)
  - [Java](#java)
  - [C# / .NET](#c--net)
  - [Go](#go)
  - [PHP](#php)
  - [Ruby](#ruby)
  - [Rust](#rust)
  - [C / C++](#c--c)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Error Observability platform is compatible with the Sentry SDK ecosystem. This allows you to use any Sentry-compatible SDK to send error reports, performance data, and custom events to your self-hosted Bugsink server.

### Key Features

- **Error Tracking**: Capture exceptions with full stack traces
- **Performance Monitoring**: Track transactions and spans for performance insights
- **Breadcrumbs**: Record user actions leading up to an error
- **User Context**: Associate errors with specific users
- **Custom Tags & Context**: Add metadata for filtering and analysis
- **Release Tracking**: Track errors by application version

---

## Quick Start

1. **Get your DSN** from the Bugsink dashboard (Project Settings → Client Keys)
2. **Install the SDK** for your language
3. **Initialize the SDK** with your DSN
4. **Start capturing errors** automatically or manually

### DSN Format

```
https://<project-key>@<hostname>/<project-id>
```

Example:
```
https://abc123def456@errors.observability.app.bauer-group.com/1
```

---

## Supported Languages

| Language | SDK Package | Example File |
|----------|-------------|--------------|
| Python | `sentry-sdk` | [python_example.py](../examples/python_example.py) |
| Node.js | `@sentry/node` | [nodejs_example.js](../examples/nodejs_example.js) |
| TypeScript | `@sentry/node` | [typescript_example.ts](../examples/typescript_example.ts) |
| Java | `io.sentry:sentry` | [JavaExample.java](../examples/JavaExample.java) |
| C# / .NET | `Sentry` | [DotNetExample.cs](../examples/DotNetExample.cs) |
| Go | `github.com/getsentry/sentry-go` | [go_example.go](../examples/go_example.go) |
| PHP | `sentry/sentry` | [php_example.php](../examples/php_example.php) |
| Ruby | `sentry-ruby` | [ruby_example.rb](../examples/ruby_example.rb) |
| Rust | `sentry` | [rust_example.rs](../examples/rust_example.rs) |
| C / C++ | `sentry-native` | [cpp_example.cpp](../examples/cpp_example.cpp) |

---

## Common Features

All SDK examples demonstrate these core features:

### 1. Initialization

```python
# Example: Python
sentry_sdk.init(
    dsn="https://key@hostname/1",
    environment="production",
    release="my-app@1.0.0",
    traces_sample_rate=0.1,
)
```

### 2. User Context

Associate errors with specific users for better debugging:

```python
sentry_sdk.set_user({
    "id": "user-123",
    "email": "user@example.com",
    "username": "johndoe"
})
```

### 3. Breadcrumbs

Track user actions leading up to an error:

```python
sentry_sdk.add_breadcrumb(
    message="User clicked checkout button",
    category="ui.click",
    level="info"
)
```

### 4. Custom Tags & Context

Add metadata for filtering in the dashboard:

```python
sentry_sdk.set_tag("feature", "checkout")
sentry_sdk.set_extra("cart_items", 3)
sentry_sdk.set_context("order", {"total": 99.99})
```

### 5. Manual Error Capture

Capture handled exceptions:

```python
try:
    risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)
```

### 6. Performance Monitoring

Track transactions for performance insights:

```python
with sentry_sdk.start_transaction(name="process_order", op="task"):
    with sentry_sdk.start_span(op="db.query"):
        fetch_order()
    with sentry_sdk.start_span(op="http.client"):
        call_payment_api()
```

---

## Language-Specific Guides

### Python

**Installation:**
```bash
pip install sentry-sdk
```

**Framework Integrations:**
- Flask: `sentry_sdk.integrations.flask.FlaskIntegration`
- Django: `sentry_sdk.integrations.django.DjangoIntegration`
- FastAPI: `sentry_sdk.integrations.starlette.StarletteIntegration`

**Example:**
```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://key@errors.observability.app.bauer-group.com/1",
    environment="production",
    release="my-app@1.0.0",
    traces_sample_rate=0.1,
    send_default_pii=False,
)
```

📁 **Full Example:** [python_example.py](../examples/python_example.py)

---

### JavaScript / Node.js

**Installation:**
```bash
npm install @sentry/node @sentry/profiling-node
```

**Framework Integrations:**
- Express: Built-in middleware
- Koa: `@sentry/koa`
- NestJS: `@sentry/nestjs`

**Example:**
```javascript
const Sentry = require("@sentry/node");

Sentry.init({
  dsn: "https://key@errors.observability.app.bauer-group.com/1",
  environment: "production",
  release: "my-app@1.0.0",
  tracesSampleRate: 0.1,
});
```

📁 **Full Example:** [nodejs_example.js](../examples/nodejs_example.js)

---

### TypeScript

**Installation:**
```bash
npm install @sentry/node @sentry/profiling-node
npm install -D typescript @types/node
```

**Example:**
```typescript
import * as Sentry from "@sentry/node";

Sentry.init({
  dsn: "https://key@errors.observability.app.bauer-group.com/1",
  environment: "production",
  release: "my-app@1.0.0",
  tracesSampleRate: 0.1,
});
```

📁 **Full Example:** [typescript_example.ts](../examples/typescript_example.ts)

---

### Java

**Maven:**
```xml
<dependency>
    <groupId>io.sentry</groupId>
    <artifactId>sentry</artifactId>
    <version>7.0.0</version>
</dependency>
```

**Gradle:**
```groovy
implementation 'io.sentry:sentry:7.0.0'
```

**Framework Integrations:**
- Spring Boot: `sentry-spring-boot-starter-jakarta`
- Log4j2: `sentry-log4j2`
- Logback: `sentry-logback`

**Example:**
```java
import io.sentry.Sentry;

Sentry.init(options -> {
    options.setDsn("https://key@errors.observability.app.bauer-group.com/1");
    options.setEnvironment("production");
    options.setRelease("my-app@1.0.0");
    options.setTracesSampleRate(0.1);
});
```

📁 **Full Example:** [JavaExample.java](../examples/JavaExample.java)

---

### C# / .NET

**NuGet:**
```bash
dotnet add package Sentry
dotnet add package Sentry.AspNetCore  # For ASP.NET Core
```

**ASP.NET Core:**
```csharp
// Program.cs
builder.WebHost.UseSentry(options => {
    options.Dsn = "https://key@errors.observability.app.bauer-group.com/1";
    options.Environment = "production";
    options.Release = "my-app@1.0.0";
    options.TracesSampleRate = 0.1;
});
```

**Console App:**
```csharp
using Sentry;

SentrySdk.Init(options => {
    options.Dsn = "https://key@errors.observability.app.bauer-group.com/1";
    options.Environment = "production";
    options.Release = "my-app@1.0.0";
});
```

📁 **Full Example:** [DotNetExample.cs](../examples/DotNetExample.cs)

---

### Go

**Installation:**
```bash
go get github.com/getsentry/sentry-go
```

**Example:**
```go
import "github.com/getsentry/sentry-go"

err := sentry.Init(sentry.ClientOptions{
    Dsn:              "https://key@errors.observability.app.bauer-group.com/1",
    Environment:      "production",
    Release:          "my-app@1.0.0",
    TracesSampleRate: 0.1,
})
```

📁 **Full Example:** [go_example.go](../examples/go_example.go)

---

### PHP

**Composer:**
```bash
composer require sentry/sentry
```

**Framework Integrations:**
- Laravel: `sentry/sentry-laravel`
- Symfony: `sentry/sentry-symfony`

**Example:**
```php
\Sentry\init([
    'dsn' => 'https://key@errors.observability.app.bauer-group.com/1',
    'environment' => 'production',
    'release' => 'my-app@1.0.0',
    'traces_sample_rate' => 0.1,
]);
```

📁 **Full Example:** [php_example.php](../examples/php_example.php)

---

### Ruby

**Gemfile:**
```ruby
gem 'sentry-ruby'
gem 'sentry-rails'  # For Rails applications
```

**Example:**
```ruby
Sentry.init do |config|
  config.dsn = 'https://key@errors.observability.app.bauer-group.com/1'
  config.environment = 'production'
  config.release = 'my-app@1.0.0'
  config.traces_sample_rate = 0.1
end
```

📁 **Full Example:** [ruby_example.rb](../examples/ruby_example.rb)

---

### Rust

**Cargo.toml:**
```toml
[dependencies]
sentry = "0.32"
```

**Example:**
```rust
let _guard = sentry::init((
    "https://key@errors.observability.app.bauer-group.com/1",
    sentry::ClientOptions {
        release: Some("my-app@1.0.0".into()),
        environment: Some("production".into()),
        traces_sample_rate: 0.1,
        ..Default::default()
    },
));
```

📁 **Full Example:** [rust_example.rs](../examples/rust_example.rs)

---

### C / C++

**CMake (FetchContent):**
```cmake
include(FetchContent)
FetchContent_Declare(
    sentry
    GIT_REPOSITORY https://github.com/getsentry/sentry-native.git
    GIT_TAG 0.7.0
)
FetchContent_MakeAvailable(sentry)
```

**Example:**
```cpp
#include <sentry.h>

sentry_options_t* options = sentry_options_new();
sentry_options_set_dsn(options, "https://key@errors.observability.app.bauer-group.com/1");
sentry_options_set_environment(options, "production");
sentry_options_set_release(options, "my-app@1.0.0");
sentry_init(options);
```

📁 **Full Example:** [cpp_example.cpp](../examples/cpp_example.cpp)

---

## Best Practices

### 1. Environment Configuration

Always use environment variables for sensitive configuration:

```bash
export SENTRY_DSN="https://key@hostname/1"
export ENVIRONMENT="production"
export APP_VERSION="1.0.0"
```

### 2. Sample Rates

Adjust sample rates for production to control costs and performance:

| Environment | Error Sample Rate | Traces Sample Rate |
|-------------|-------------------|-------------------|
| Development | 1.0 (100%) | 1.0 (100%) |
| Staging | 1.0 (100%) | 0.5 (50%) |
| Production | 1.0 (100%) | 0.1 (10%) |

### 3. Data Sanitization

Always sanitize sensitive data before sending:

```python
def before_send(event, hint):
    # Remove sensitive headers
    if event.get("request", {}).get("headers"):
        for header in ["Authorization", "Cookie"]:
            if header in event["request"]["headers"]:
                event["request"]["headers"][header] = "[REDACTED]"
    return event

sentry_sdk.init(before_send=before_send)
```

### 4. Performance Monitoring

Name transactions consistently:

- HTTP endpoints: Use the route pattern (e.g., `GET /api/users/:id`)
- Background jobs: Use the job name (e.g., `ProcessOrderJob`)
- Tasks: Use a descriptive name (e.g., `generate_monthly_report`)

### 5. Release Tracking

Always set the release version to track errors across deployments:

```python
sentry_sdk.init(release="my-app@1.2.3")
```

---

## Troubleshooting

### Events Not Appearing

1. **Check DSN**: Verify the DSN is correct and accessible
2. **Check Sample Rate**: Ensure `sample_rate` is > 0
3. **Flush Events**: Call `flush()` before application exit
4. **Check Network**: Verify the application can reach the Bugsink server

### Debug Mode

Enable debug mode to see SDK logs:

```python
sentry_sdk.init(debug=True)
```

### Common Issues

| Issue | Solution |
|-------|----------|
| SSL Certificate Error | Add server's CA to trusted certificates |
| Connection Timeout | Check firewall rules and network connectivity |
| Events Dropped | Increase `max_queue_size` or reduce sample rate |
| Missing Stack Traces | Enable `attach_stacktrace=True` |

---

## Additional Resources

- [Sentry Documentation](https://docs.sentry.io/)
- [Bugsink Configuration](./BUGSINK-CONFIGURATION.md)
- [SDK Configuration Reference](./BUGSINK-SDK-CONFIGURATION.md)
- [Quick Start Guide](./BUGSINK-QUICKSTART.md)

---

*Generated for Error Observability Platform*
