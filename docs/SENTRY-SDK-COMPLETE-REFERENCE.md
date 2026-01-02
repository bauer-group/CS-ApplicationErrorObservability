# Complete Sentry SDK Reference for Bugsink

Bugsink is fully compatible with all official Sentry SDKs. This comprehensive guide covers installation, configuration, and advanced usage for every supported platform.

> **Migration from Sentry?** Simply update your DSN to point to your Bugsink instance. No code changes required!

## Table of Contents

- [Compatibility Overview](#compatibility-overview)
- [DSN Configuration](#dsn-configuration)
- [Backend Languages](#backend-languages)
  - [Python](#python)
  - [Node.js](#nodejs)
  - [PHP](#php)
  - [Ruby](#ruby)
  - [Go](#go)
  - [Java](#java)
  - [Kotlin](#kotlin)
  - [.NET / C#](#net--c)
  - [Rust](#rust)
  - [Elixir](#elixir)
- [Frontend / JavaScript](#frontend--javascript)
  - [Browser JavaScript](#browser-javascript)
  - [React](#react)
  - [Vue.js](#vuejs)
  - [Angular](#angular)
  - [Svelte](#svelte)
  - [Next.js](#nextjs)
  - [Nuxt](#nuxt)
- [Mobile Development](#mobile-development)
  - [React Native](#react-native)
  - [Flutter / Dart](#flutter--dart)
  - [Android (Java/Kotlin)](#android-javakotlin)
  - [iOS / macOS (Swift)](#ios--macos-swift)
- [Game Development](#game-development)
  - [Unity](#unity)
  - [Unreal Engine](#unreal-engine)
  - [Godot](#godot)
- [Desktop / Native](#desktop--native)
  - [Electron](#electron)
  - [Native (C/C++)](#native-cc)
- [Framework Integrations](#framework-integrations)
  - [Django](#django)
  - [Flask](#flask)
  - [FastAPI](#fastapi)
  - [Express.js](#expressjs)
  - [Fastify](#fastify)
  - [NestJS](#nestjs)
  - [Laravel](#laravel)
  - [Symfony](#symfony)
  - [Rails](#rails)
  - [Spring Boot](#spring-boot)
  - [ASP.NET Core](#aspnet-core)
  - [Gin (Go)](#gin-go)
  - [Echo (Go)](#echo-go)
- [Serverless](#serverless)
  - [AWS Lambda](#aws-lambda)
  - [Google Cloud Functions](#google-cloud-functions)
  - [Azure Functions](#azure-functions)
  - [Vercel](#vercel)
  - [Cloudflare Workers](#cloudflare-workers)
- [Configuration Options](#configuration-options)
- [Best Practices](#best-practices)

---

## Compatibility Overview

Bugsink receives error reports via the same JSON payload format used by Sentry. This means:

- **Zero code changes** when migrating from Sentry
- **All official SDKs** work out of the box
- **Community SDKs** are also supported
- **No forks or patches** required

The Bugsink team actively monitors SDK developments to maintain compatibility.

### Verified SDKs

The following SDKs have been explicitly verified with Bugsink:

| SDK | Status | Notes |
|-----|--------|-------|
| Python | ✅ Verified | Full feature support |
| JavaScript (Browser) | ✅ Verified | Full feature support |
| Node.js | ✅ Verified | Full feature support |
| PHP | ✅ Verified | Full feature support |
| Go | ✅ Compatible | Full feature support |
| Java | ✅ Compatible | Full feature support |
| .NET | ✅ Compatible | Full feature support |
| Ruby | ✅ Compatible | Full feature support |
| Rust | ✅ Compatible | Community SDK |
| Elixir | ✅ Compatible | Community SDK |

---

## DSN Configuration

Your Data Source Name (DSN) is the connection string that tells the SDK where to send events.

### DSN Format

```
https://<public-key>@<hostname>/<project-id>
```

### Example

```
https://a1b2c3d4e5f6@bugsink.yourcompany.com/1
```

### Finding Your DSN

1. Log in to Bugsink
2. Navigate to your project
3. Go to **Settings** → **Client Keys (DSN)**
4. Copy the DSN

---

## Backend Languages

### Python

The Python SDK is the most mature and feature-rich SDK.

#### Installation

```bash
pip install sentry-sdk
```

#### Basic Setup

```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://your-key@bugsink.yourcompany.com/1",

    # Environment and Release
    environment="production",
    release="myapp@1.2.3",

    # Sample rates
    sample_rate=1.0,              # Error events (100%)
    traces_sample_rate=0.1,       # Performance traces (10%)
    profiles_sample_rate=0.1,     # Profiling (10%)

    # Additional options
    send_default_pii=False,       # Don't send PII by default
    attach_stacktrace=True,       # Always attach stack traces
    max_breadcrumbs=100,          # Breadcrumb limit
)
```

#### Manual Error Capture

```python
import sentry_sdk

# Capture exception
try:
    dangerous_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)

# Capture message
sentry_sdk.capture_message("Something noteworthy happened", level="info")

# Capture with extra context
with sentry_sdk.push_scope() as scope:
    scope.set_tag("feature", "payment")
    scope.set_extra("order_id", 12345)
    scope.set_user({"id": "user-123", "email": "user@example.com"})
    sentry_sdk.capture_message("Payment processed")
```

#### Context Management

```python
import sentry_sdk

# Set user context
sentry_sdk.set_user({
    "id": "12345",
    "email": "user@example.com",
    "username": "johndoe",
    "ip_address": "{{auto}}",  # Auto-detect IP
})

# Set tags (searchable)
sentry_sdk.set_tag("customer_tier", "enterprise")
sentry_sdk.set_tag("region", "eu-west")

# Set extra context (not searchable)
sentry_sdk.set_extra("shopping_cart", ["item1", "item2"])

# Set context (grouped extra data)
sentry_sdk.set_context("order", {
    "id": "ORD-123",
    "total": 99.99,
    "currency": "EUR",
})

# Add breadcrumb
sentry_sdk.add_breadcrumb(
    category="auth",
    message="User logged in",
    level="info",
    data={"method": "oauth"},
)
```

#### Filtering Events

```python
import sentry_sdk

def before_send(event, hint):
    # Filter out specific exceptions
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        if isinstance(exc_value, KeyboardInterrupt):
            return None  # Don't send

    # Remove sensitive data
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        if "Authorization" in headers:
            headers["Authorization"] = "[Filtered]"

    # Filter by environment
    if event.get("environment") == "development":
        return None

    return event

def before_send_transaction(event, hint):
    # Filter transactions by name
    if event.get("transaction") == "/health":
        return None
    return event

sentry_sdk.init(
    dsn="...",
    before_send=before_send,
    before_send_transaction=before_send_transaction,
)
```

#### Async Support

```python
import asyncio
import sentry_sdk

sentry_sdk.init(dsn="...")

async def main():
    try:
        await async_operation()
    except Exception:
        sentry_sdk.capture_exception()

asyncio.run(main())
```

---

### Node.js

#### Installation

```bash
npm install @sentry/node
# or
yarn add @sentry/node
```

#### Basic Setup

```javascript
const Sentry = require("@sentry/node");

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",

    // Environment and Release
    environment: "production",
    release: "myapp@1.2.3",

    // Sample rates
    sampleRate: 1.0,
    tracesSampleRate: 0.1,
    profilesSampleRate: 0.1,

    // Integrations
    integrations: [
        Sentry.httpIntegration(),
        Sentry.nativeNodeFetchIntegration(),
    ],
});
```

#### ES Modules

```javascript
import * as Sentry from "@sentry/node";

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    environment: process.env.NODE_ENV,
    release: process.env.npm_package_version,
});
```

#### Error Handling

```javascript
const Sentry = require("@sentry/node");

// Capture exception
try {
    throw new Error("Something went wrong");
} catch (error) {
    Sentry.captureException(error);
}

// Capture message
Sentry.captureMessage("User completed onboarding", "info");

// Capture with scope
Sentry.withScope((scope) => {
    scope.setTag("section", "checkout");
    scope.setExtra("cart_items", 3);
    scope.setUser({ id: "user-123" });
    Sentry.captureException(new Error("Checkout failed"));
});
```

#### Async Context

```javascript
const Sentry = require("@sentry/node");

async function processOrder(orderId) {
    return Sentry.withScope(async (scope) => {
        scope.setTag("order_id", orderId);

        try {
            await chargeCustomer(orderId);
            await sendConfirmation(orderId);
        } catch (error) {
            Sentry.captureException(error);
            throw error;
        }
    });
}
```

#### Graceful Shutdown

```javascript
const Sentry = require("@sentry/node");

process.on("SIGTERM", async () => {
    console.log("Shutting down...");
    await Sentry.close(2000); // 2 second timeout
    process.exit(0);
});
```

---

### PHP

#### Installation

```bash
composer require sentry/sentry
```

#### Basic Setup

```php
<?php
require_once 'vendor/autoload.php';

\Sentry\init([
    'dsn' => 'https://your-key@bugsink.yourcompany.com/1',
    'environment' => 'production',
    'release' => 'myapp@1.2.3',
    'sample_rate' => 1.0,
    'traces_sample_rate' => 0.1,
]);
```

#### Error Handling

```php
<?php
// Automatic exception handling
try {
    throw new \Exception('Something went wrong');
} catch (\Throwable $e) {
    \Sentry\captureException($e);
}

// Capture message
\Sentry\captureMessage('User signed up', \Sentry\Severity::info());

// With scope
\Sentry\withScope(function (\Sentry\State\Scope $scope): void {
    $scope->setTag('feature', 'registration');
    $scope->setUser(['id' => 'user-123', 'email' => 'user@example.com']);
    $scope->setExtra('plan', 'premium');

    \Sentry\captureMessage('Premium signup completed');
});
```

#### Context

```php
<?php
// Configure scope
\Sentry\configureScope(function (\Sentry\State\Scope $scope): void {
    $scope->setUser([
        'id' => $_SESSION['user_id'],
        'email' => $_SESSION['email'],
    ]);

    $scope->setTag('page', 'checkout');

    $scope->setContext('order', [
        'id' => $orderId,
        'total' => $total,
    ]);
});

// Add breadcrumb
\Sentry\addBreadcrumb(new \Sentry\Breadcrumb(
    \Sentry\Breadcrumb::LEVEL_INFO,
    \Sentry\Breadcrumb::TYPE_USER,
    'auth',
    'User authenticated'
));
```

#### Error Handler Registration

```php
<?php
// Register as global error handler
set_exception_handler(function (\Throwable $e): void {
    \Sentry\captureException($e);
    throw $e; // Re-throw after capturing
});

set_error_handler(function (int $errno, string $errstr, string $errfile, int $errline): bool {
    if (!(error_reporting() & $errno)) {
        return false;
    }

    \Sentry\captureException(new \ErrorException($errstr, 0, $errno, $errfile, $errline));
    return true;
});
```

---

### Ruby

#### Installation

```bash
gem install sentry-ruby
```

Or in Gemfile:
```ruby
gem "sentry-ruby"
```

#### Basic Setup

```ruby
require "sentry-ruby"

Sentry.init do |config|
    config.dsn = "https://your-key@bugsink.yourcompany.com/1"
    config.environment = ENV["RACK_ENV"] || "development"
    config.release = "myapp@1.2.3"
    config.sample_rate = 1.0
    config.traces_sample_rate = 0.1

    # Breadcrumbs
    config.breadcrumbs_logger = [:sentry_logger, :http_logger]
    config.max_breadcrumbs = 100
end
```

#### Error Handling

```ruby
require "sentry-ruby"

# Capture exception
begin
    raise "Something went wrong"
rescue => e
    Sentry.capture_exception(e)
end

# Capture message
Sentry.capture_message("User completed checkout", level: :info)

# With scope
Sentry.with_scope do |scope|
    scope.set_tags(feature: "payment", region: "eu")
    scope.set_user(id: "user-123", email: "user@example.com")
    scope.set_extras(order_id: 12345)

    Sentry.capture_message("Payment processed")
end
```

#### Context Configuration

```ruby
# Set user
Sentry.set_user(
    id: current_user.id,
    email: current_user.email,
    username: current_user.username
)

# Set tags
Sentry.set_tags(
    customer_tier: "enterprise",
    region: "eu-west"
)

# Set context
Sentry.set_context("order", {
    id: order.id,
    total: order.total,
    currency: order.currency
})

# Add breadcrumb
Sentry.add_breadcrumb(
    category: "auth",
    message: "User logged in",
    level: :info,
    data: { method: "oauth" }
)
```

---

### Go

#### Installation

```bash
go get github.com/getsentry/sentry-go
```

#### Basic Setup

```go
package main

import (
    "log"
    "time"

    "github.com/getsentry/sentry-go"
)

func main() {
    err := sentry.Init(sentry.ClientOptions{
        Dsn:              "https://your-key@bugsink.yourcompany.com/1",
        Environment:      "production",
        Release:          "myapp@1.2.3",
        TracesSampleRate: 0.1,

        // Enable stack trace for all messages
        AttachStacktrace: true,

        // Debug mode (logs SDK operations)
        Debug: false,
    })
    if err != nil {
        log.Fatalf("sentry.Init: %s", err)
    }

    // Flush buffered events before exit
    defer sentry.Flush(2 * time.Second)

    // Your application code
    run()
}
```

#### Error Handling

```go
package main

import (
    "errors"
    "github.com/getsentry/sentry-go"
)

func processOrder(orderID string) error {
    // Capture exception
    defer func() {
        if r := recover(); r != nil {
            sentry.CurrentHub().Recover(r)
            sentry.Flush(time.Second * 2)
        }
    }()

    if err := validateOrder(orderID); err != nil {
        sentry.CaptureException(err)
        return err
    }

    return nil
}

// Capture message
func logEvent(message string) {
    sentry.CaptureMessage(message)
}

// With scope
func processWithContext(userID string, orderID string) {
    sentry.WithScope(func(scope *sentry.Scope) {
        scope.SetTag("feature", "checkout")
        scope.SetUser(sentry.User{ID: userID})
        scope.SetExtra("order_id", orderID)

        if err := process(); err != nil {
            sentry.CaptureException(err)
        }
    })
}
```

#### Context

```go
// Configure hub
hub := sentry.CurrentHub()

// Set user
hub.ConfigureScope(func(scope *sentry.Scope) {
    scope.SetUser(sentry.User{
        ID:        "user-123",
        Email:     "user@example.com",
        IPAddress: "{{auto}}",
    })
})

// Set tags
hub.ConfigureScope(func(scope *sentry.Scope) {
    scope.SetTag("region", "eu-west")
    scope.SetTag("customer_tier", "enterprise")
})

// Add breadcrumb
sentry.AddBreadcrumb(&sentry.Breadcrumb{
    Category: "auth",
    Message:  "User logged in",
    Level:    sentry.LevelInfo,
    Data: map[string]interface{}{
        "method": "oauth",
    },
})
```

---

### Java

#### Installation (Gradle)

```groovy
implementation 'io.sentry:sentry:7.+'
```

#### Installation (Maven)

```xml
<dependency>
    <groupId>io.sentry</groupId>
    <artifactId>sentry</artifactId>
    <version>7.+</version>
</dependency>
```

#### Basic Setup

```java
import io.sentry.Sentry;
import io.sentry.SentryLevel;

public class Application {
    public static void main(String[] args) {
        Sentry.init(options -> {
            options.setDsn("https://your-key@bugsink.yourcompany.com/1");
            options.setEnvironment("production");
            options.setRelease("myapp@1.2.3");
            options.setTracesSampleRate(0.1);
            options.setDebug(false);
        });

        // Application code
        run();
    }
}
```

#### Error Handling

```java
import io.sentry.Sentry;
import io.sentry.SentryLevel;

public class OrderService {
    public void processOrder(String orderId) {
        try {
            // Business logic
            doProcessOrder(orderId);
        } catch (Exception e) {
            // Capture exception
            Sentry.captureException(e);
            throw e;
        }
    }

    public void logEvent(String message) {
        // Capture message
        Sentry.captureMessage(message, SentryLevel.INFO);
    }

    public void processWithContext(String userId, String orderId) {
        // With scope
        Sentry.withScope(scope -> {
            scope.setTag("feature", "checkout");
            scope.setExtra("order_id", orderId);

            io.sentry.protocol.User user = new io.sentry.protocol.User();
            user.setId(userId);
            scope.setUser(user);

            try {
                doProcessOrder(orderId);
            } catch (Exception e) {
                Sentry.captureException(e);
            }
        });
    }
}
```

#### Context Configuration

```java
import io.sentry.Sentry;
import io.sentry.protocol.User;

// Set user
Sentry.configureScope(scope -> {
    User user = new User();
    user.setId("user-123");
    user.setEmail("user@example.com");
    user.setUsername("johndoe");
    scope.setUser(user);
});

// Set tags
Sentry.configureScope(scope -> {
    scope.setTag("region", "eu-west");
    scope.setTag("customer_tier", "enterprise");
});

// Set context
Sentry.configureScope(scope -> {
    Map<String, Object> orderContext = new HashMap<>();
    orderContext.put("id", orderId);
    orderContext.put("total", 99.99);
    scope.setContexts("order", orderContext);
});

// Add breadcrumb
Sentry.addBreadcrumb(
    Breadcrumb.info("User logged in")
        .setCategory("auth")
        .setData("method", "oauth")
);
```

---

### Kotlin

#### Installation

```kotlin
// build.gradle.kts
implementation("io.sentry:sentry:7.+")
```

#### Basic Setup

```kotlin
import io.sentry.Sentry

fun main() {
    Sentry.init { options ->
        options.dsn = "https://your-key@bugsink.yourcompany.com/1"
        options.environment = "production"
        options.release = "myapp@1.2.3"
        options.tracesSampleRate = 0.1
    }

    // Application code
    run()
}
```

#### Error Handling

```kotlin
import io.sentry.Sentry
import io.sentry.SentryLevel

class OrderService {
    fun processOrder(orderId: String) {
        try {
            doProcessOrder(orderId)
        } catch (e: Exception) {
            Sentry.captureException(e)
            throw e
        }
    }

    fun processWithContext(userId: String, orderId: String) {
        Sentry.withScope { scope ->
            scope.setTag("feature", "checkout")
            scope.setExtra("order_id", orderId)
            scope.user = io.sentry.protocol.User().apply {
                id = userId
            }

            try {
                doProcessOrder(orderId)
            } catch (e: Exception) {
                Sentry.captureException(e)
            }
        }
    }
}
```

---

### .NET / C#

#### Installation

```bash
dotnet add package Sentry
```

#### Basic Setup

```csharp
using Sentry;

class Program
{
    static void Main()
    {
        using (SentrySdk.Init(options =>
        {
            options.Dsn = "https://your-key@bugsink.yourcompany.com/1";
            options.Environment = "production";
            options.Release = "myapp@1.2.3";
            options.TracesSampleRate = 0.1;
            options.Debug = false;
        }))
        {
            // Application code
            Run();
        }
    }
}
```

#### Error Handling

```csharp
using Sentry;

public class OrderService
{
    public void ProcessOrder(string orderId)
    {
        try
        {
            DoProcessOrder(orderId);
        }
        catch (Exception ex)
        {
            SentrySdk.CaptureException(ex);
            throw;
        }
    }

    public void ProcessWithContext(string userId, string orderId)
    {
        SentrySdk.WithScope(scope =>
        {
            scope.SetTag("feature", "checkout");
            scope.SetExtra("order_id", orderId);
            scope.User = new User { Id = userId };

            try
            {
                DoProcessOrder(orderId);
            }
            catch (Exception ex)
            {
                SentrySdk.CaptureException(ex);
            }
        });
    }
}
```

#### Context Configuration

```csharp
using Sentry;

// Set user
SentrySdk.ConfigureScope(scope =>
{
    scope.User = new User
    {
        Id = "user-123",
        Email = "user@example.com",
        Username = "johndoe"
    };
});

// Set tags
SentrySdk.ConfigureScope(scope =>
{
    scope.SetTag("region", "eu-west");
    scope.SetTag("customer_tier", "enterprise");
});

// Add breadcrumb
SentrySdk.AddBreadcrumb(
    message: "User logged in",
    category: "auth",
    level: BreadcrumbLevel.Info,
    data: new Dictionary<string, string> { { "method", "oauth" } }
);
```

---

### Rust

#### Installation

```toml
# Cargo.toml
[dependencies]
sentry = "0.32"
```

#### Basic Setup

```rust
use sentry;

fn main() {
    let _guard = sentry::init((
        "https://your-key@bugsink.yourcompany.com/1",
        sentry::ClientOptions {
            release: sentry::release_name!(),
            environment: Some("production".into()),
            sample_rate: 1.0,
            traces_sample_rate: 0.1,
            ..Default::default()
        },
    ));

    // Application code
    run();
}
```

#### Error Handling

```rust
use sentry;

fn process_order(order_id: &str) -> Result<(), Box<dyn std::error::Error>> {
    match do_process_order(order_id) {
        Ok(_) => Ok(()),
        Err(e) => {
            sentry::capture_error(&e);
            Err(e)
        }
    }
}

// Capture message
fn log_event(message: &str) {
    sentry::capture_message(message, sentry::Level::Info);
}

// With scope
fn process_with_context(user_id: &str, order_id: &str) {
    sentry::with_scope(
        |scope| {
            scope.set_tag("feature", "checkout");
            scope.set_extra("order_id", order_id.into());
            scope.set_user(Some(sentry::User {
                id: Some(user_id.to_string()),
                ..Default::default()
            }));
        },
        || {
            if let Err(e) = process() {
                sentry::capture_error(&e);
            }
        },
    );
}
```

---

### Elixir

#### Installation

```elixir
# mix.exs
defp deps do
  [
    {:sentry, "~> 10.0"},
    {:jason, "~> 1.1"},
    {:hackney, "~> 1.8"}
  ]
end
```

#### Configuration

```elixir
# config/config.exs
config :sentry,
  dsn: "https://your-key@bugsink.yourcompany.com/1",
  environment_name: Mix.env(),
  release: "myapp@1.2.3",
  enable_source_code_context: true,
  root_source_code_paths: [File.cwd!()]
```

#### Error Handling

```elixir
# Manual capture
try do
  dangerous_operation()
rescue
  e ->
    Sentry.capture_exception(e, stacktrace: __STACKTRACE__)
    reraise e, __STACKTRACE__
end

# Capture message
Sentry.capture_message("User completed checkout", level: :info)

# With context
Sentry.Context.set_user_context(%{
  id: user.id,
  email: user.email
})

Sentry.Context.set_tags_context(%{
  feature: "checkout",
  region: "eu-west"
})

Sentry.Context.set_extra_context(%{
  order_id: order.id
})
```

#### Plug Integration

```elixir
# In your Phoenix endpoint
plug Sentry.PlugContext
plug Sentry.PlugCapture
```

---

## Frontend / JavaScript

### Browser JavaScript

#### Installation

```bash
npm install @sentry/browser
```

#### Basic Setup

```javascript
import * as Sentry from "@sentry/browser";

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    environment: "production",
    release: "myapp@1.2.3",

    // Sample rates
    sampleRate: 1.0,
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,

    // Integrations
    integrations: [
        Sentry.browserTracingIntegration(),
        Sentry.replayIntegration(),
    ],
});
```

#### Error Handling

```javascript
import * as Sentry from "@sentry/browser";

// Capture exception
try {
    throw new Error("Something went wrong");
} catch (error) {
    Sentry.captureException(error);
}

// Capture message
Sentry.captureMessage("User completed checkout", "info");

// With scope
Sentry.withScope((scope) => {
    scope.setTag("section", "checkout");
    scope.setExtra("cart_items", 3);
    scope.setUser({ id: "user-123" });
    Sentry.captureException(new Error("Checkout failed"));
});
```

#### Context

```javascript
import * as Sentry from "@sentry/browser";

// Set user
Sentry.setUser({
    id: "user-123",
    email: "user@example.com",
    username: "johndoe",
});

// Set tags
Sentry.setTag("feature", "checkout");
Sentry.setTags({ region: "eu", tier: "premium" });

// Set extra
Sentry.setExtra("cart_items", 3);
Sentry.setExtras({ order_id: "ORD-123", total: 99.99 });

// Set context
Sentry.setContext("order", {
    id: "ORD-123",
    total: 99.99,
    currency: "EUR",
});

// Add breadcrumb
Sentry.addBreadcrumb({
    category: "auth",
    message: "User logged in",
    level: "info",
    data: { method: "oauth" },
});
```

---

### React

#### Installation

```bash
npm install @sentry/react
```

#### Basic Setup

```jsx
import * as Sentry from "@sentry/react";
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    environment: "production",
    release: "myapp@1.2.3",
    integrations: [
        Sentry.browserTracingIntegration(),
        Sentry.replayIntegration(),
    ],
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
});

ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
```

#### Error Boundary

```jsx
import * as Sentry from "@sentry/react";

function FallbackComponent({ error, componentStack, resetError }) {
    return (
        <div className="error-boundary">
            <h2>Something went wrong</h2>
            <details>
                <summary>Error details</summary>
                <pre>{error.toString()}</pre>
                <pre>{componentStack}</pre>
            </details>
            <button onClick={resetError}>Try again</button>
        </div>
    );
}

function App() {
    return (
        <Sentry.ErrorBoundary
            fallback={FallbackComponent}
            showDialog={true}
            dialogOptions={{
                title: "It looks like we're having issues.",
                subtitle: "Our team has been notified.",
            }}
        >
            <MainContent />
        </Sentry.ErrorBoundary>
    );
}
```

#### React Router Integration

```jsx
import * as Sentry from "@sentry/react";
import { createBrowserRouter } from "react-router-dom";

const sentryCreateBrowserRouter = Sentry.wrapCreateBrowserRouter(
    createBrowserRouter
);

const router = sentryCreateBrowserRouter([
    {
        path: "/",
        element: <Root />,
        children: [
            { path: "dashboard", element: <Dashboard /> },
            { path: "orders/:id", element: <OrderDetail /> },
        ],
    },
]);
```

#### Component Profiler

```jsx
import * as Sentry from "@sentry/react";

// Profile specific components
const ProfiledComponent = Sentry.withProfiler(MyComponent);

// Or use the hook
function MyComponent() {
    return <Sentry.Profiler name="MyComponent">
        <div>Content</div>
    </Sentry.Profiler>;
}
```

---

### Vue.js

#### Installation

```bash
npm install @sentry/vue
```

#### Vue 3 Setup

```javascript
import * as Sentry from "@sentry/vue";
import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";

const app = createApp(App);

const router = createRouter({
    history: createWebHistory(),
    routes: [/* your routes */],
});

Sentry.init({
    app,
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    environment: "production",
    release: "myapp@1.2.3",
    integrations: [
        Sentry.browserTracingIntegration({ router }),
        Sentry.replayIntegration(),
    ],
    tracesSampleRate: 0.1,
    tracePropagationTargets: ["localhost", /^https:\/\/api\.yourcompany\.com/],
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
});

app.use(router);
app.mount("#app");
```

#### Vue 2 Setup

```javascript
import * as Sentry from "@sentry/vue";
import Vue from "vue";
import VueRouter from "vue-router";

const router = new VueRouter({/* config */});

Sentry.init({
    Vue,
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    integrations: [
        Sentry.browserTracingIntegration({ router }),
    ],
    tracesSampleRate: 0.1,
});

new Vue({
    router,
    render: h => h(App),
}).$mount("#app");
```

---

### Angular

#### Installation

```bash
npm install @sentry/angular
```

#### Setup

```typescript
// main.ts
import * as Sentry from "@sentry/angular";
import { platformBrowserDynamic } from "@angular/platform-browser-dynamic";
import { AppModule } from "./app/app.module";

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    environment: "production",
    release: "myapp@1.2.3",
    integrations: [
        Sentry.browserTracingIntegration(),
        Sentry.replayIntegration(),
    ],
    tracesSampleRate: 0.1,
});

platformBrowserDynamic()
    .bootstrapModule(AppModule)
    .catch(err => console.error(err));
```

#### Module Configuration

```typescript
// app.module.ts
import * as Sentry from "@sentry/angular";
import { ErrorHandler, NgModule } from "@angular/core";
import { Router } from "@angular/router";

@NgModule({
    providers: [
        {
            provide: ErrorHandler,
            useValue: Sentry.createErrorHandler({
                showDialog: true,
            }),
        },
        {
            provide: Sentry.TraceService,
            deps: [Router],
        },
    ],
})
export class AppModule {
    constructor(trace: Sentry.TraceService) {}
}
```

---

### Svelte

#### Installation

```bash
npm install @sentry/svelte
```

#### Setup

```javascript
// main.js
import * as Sentry from "@sentry/svelte";
import App from "./App.svelte";

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    environment: "production",
    release: "myapp@1.2.3",
    integrations: [
        Sentry.browserTracingIntegration(),
        Sentry.replayIntegration(),
    ],
    tracesSampleRate: 0.1,
});

const app = new App({
    target: document.getElementById("app"),
});

export default app;
```

---

### Next.js

#### Installation

```bash
npm install @sentry/nextjs
npx @sentry/wizard@latest -i nextjs
```

#### Configuration Files

```javascript
// sentry.client.config.js
import * as Sentry from "@sentry/nextjs";

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    environment: process.env.NODE_ENV,
    release: process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA,
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    integrations: [
        Sentry.replayIntegration(),
    ],
});
```

```javascript
// sentry.server.config.js
import * as Sentry from "@sentry/nextjs";

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    environment: process.env.NODE_ENV,
    tracesSampleRate: 0.1,
});
```

```javascript
// sentry.edge.config.js
import * as Sentry from "@sentry/nextjs";

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    tracesSampleRate: 0.1,
});
```

#### Next.js Config

```javascript
// next.config.js
const { withSentryConfig } = require("@sentry/nextjs");

const nextConfig = {
    // Your Next.js config
};

module.exports = withSentryConfig(nextConfig, {
    silent: true,
    org: "your-org",
    project: "your-project",
});
```

---

### Nuxt

#### Installation

```bash
npm install @sentry/nuxt
```

#### Nuxt 3 Setup

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
    modules: ["@sentry/nuxt/module"],
    sentry: {
        dsn: "https://your-key@bugsink.yourcompany.com/1",
    },
    sourcemap: {
        client: true,
    },
});
```

```typescript
// sentry.client.config.ts
import * as Sentry from "@sentry/nuxt";

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
});
```

---

## Mobile Development

### React Native

#### Installation

```bash
npm install @sentry/react-native
npx @sentry/wizard@latest -i reactNative
```

#### Setup

```javascript
import * as Sentry from "@sentry/react-native";

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    environment: __DEV__ ? "development" : "production",
    tracesSampleRate: 0.1,

    // Enable native crash reporting
    enableNative: true,
    enableNativeCrashHandling: true,

    // Enable auto session tracking
    enableAutoSessionTracking: true,
});
```

#### Wrap App

```javascript
import * as Sentry from "@sentry/react-native";

export default Sentry.wrap(App);
```

---

### Flutter / Dart

#### Installation

```yaml
# pubspec.yaml
dependencies:
  sentry_flutter: ^7.0.0
```

#### Setup

```dart
import 'package:sentry_flutter/sentry_flutter.dart';

Future<void> main() async {
    await SentryFlutter.init(
        (options) {
            options.dsn = 'https://your-key@bugsink.yourcompany.com/1';
            options.environment = 'production';
            options.release = 'myapp@1.2.3';
            options.tracesSampleRate = 0.1;
        },
        appRunner: () => runApp(MyApp()),
    );
}
```

#### Error Handling

```dart
import 'package:sentry_flutter/sentry_flutter.dart';

// Capture exception
try {
    throw Exception('Something went wrong');
} catch (exception, stackTrace) {
    await Sentry.captureException(
        exception,
        stackTrace: stackTrace,
    );
}

// Capture message
await Sentry.captureMessage('User completed checkout');

// With scope
await Sentry.configureScope((scope) {
    scope.setTag('feature', 'checkout');
    scope.setUser(SentryUser(id: 'user-123'));
});
```

---

### Android (Java/Kotlin)

#### Installation (Gradle)

```groovy
// build.gradle (app)
plugins {
    id "io.sentry.android.gradle" version "4.+"
}

dependencies {
    implementation 'io.sentry:sentry-android:7.+'
}
```

#### Setup

```kotlin
// Application class
import io.sentry.android.core.SentryAndroid

class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()

        SentryAndroid.init(this) { options ->
            options.dsn = "https://your-key@bugsink.yourcompany.com/1"
            options.environment = if (BuildConfig.DEBUG) "development" else "production"
            options.release = "${BuildConfig.APPLICATION_ID}@${BuildConfig.VERSION_NAME}"
            options.tracesSampleRate = 0.1
            options.isAnrEnabled = true
            options.anrTimeoutIntervalMillis = 5000
        }
    }
}
```

---

### iOS / macOS (Swift)

#### Installation (SPM)

```swift
// Package.swift
dependencies: [
    .package(url: "https://github.com/getsentry/sentry-cocoa", from: "8.0.0")
]
```

#### Installation (CocoaPods)

```ruby
# Podfile
pod 'Sentry', '~> 8.0'
```

#### Setup

```swift
import Sentry

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {
        SentrySDK.start { options in
            options.dsn = "https://your-key@bugsink.yourcompany.com/1"
            options.environment = "production"
            options.releaseName = "myapp@1.2.3"
            options.tracesSampleRate = 0.1
            options.enableAutoSessionTracking = true
            options.attachScreenshot = true
            options.attachViewHierarchy = true
        }

        return true
    }
}
```

#### Error Handling

```swift
import Sentry

// Capture exception
do {
    try riskyOperation()
} catch {
    SentrySDK.capture(error: error)
}

// Capture message
SentrySDK.capture(message: "User completed checkout")

// With scope
SentrySDK.configureScope { scope in
    scope.setTag(value: "checkout", key: "feature")
    scope.setUser(User(userId: "user-123"))
}
```

---

## Game Development

### Unity

#### Installation

Use the Unity Package Manager with the Sentry Unity SDK.

#### Setup

```csharp
using Sentry.Unity;
using UnityEngine;

public class SentryInit : MonoBehaviour
{
    void Awake()
    {
        SentryUnity.Init(options =>
        {
            options.Dsn = "https://your-key@bugsink.yourcompany.com/1";
            options.Environment = Debug.isDebugBuild ? "development" : "production";
            options.Release = Application.version;
            options.TracesSampleRate = 0.1;

            // Unity-specific options
            options.AttachScreenshot = true;
            options.CaptureInEditor = true;
        });
    }
}
```

---

### Unreal Engine

#### Setup

Configure via Project Settings → Plugins → Sentry:

- **DSN:** `https://your-key@bugsink.yourcompany.com/1`
- **Environment:** Production
- **Enable Automatic Crash Capturing:** Yes

#### Blueprint Integration

Use the Sentry Blueprint Library nodes for capturing events.

---

### Godot

#### Installation

Add the Sentry GDScript SDK to your project.

#### Setup

```gdscript
extends Node

func _ready():
    var sentry = Sentry.new()
    sentry.init({
        "dsn": "https://your-key@bugsink.yourcompany.com/1",
        "environment": "production",
        "release": ProjectSettings.get_setting("application/config/version")
    })
```

---

## Desktop / Native

### Electron

#### Installation

```bash
npm install @sentry/electron
```

#### Main Process

```javascript
// main.js
const Sentry = require("@sentry/electron/main");

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    environment: process.env.NODE_ENV,
    release: app.getVersion(),
});
```

#### Renderer Process

```javascript
// renderer.js
import * as Sentry from "@sentry/electron/renderer";

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
});
```

---

### Native (C/C++)

#### Installation

Use the Sentry Native SDK from GitHub releases.

#### Setup

```c
#include <sentry.h>

int main(int argc, char *argv[]) {
    sentry_options_t *options = sentry_options_new();
    sentry_options_set_dsn(options, "https://your-key@bugsink.yourcompany.com/1");
    sentry_options_set_environment(options, "production");
    sentry_options_set_release(options, "myapp@1.2.3");
    sentry_init(options);

    // Application code
    run();

    sentry_close();
    return 0;
}
```

---

## Framework Integrations

### Django

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="https://your-key@bugsink.yourcompany.com/1",
    integrations=[
        DjangoIntegration(
            transaction_style="url",
            middleware_spans=True,
            signals_spans=True,
            cache_spans=True,
        ),
    ],
    traces_sample_rate=0.1,
    send_default_pii=True,

    # Associate users with errors
    auto_session_tracking=True,
)
```

---

### Flask

```python
from flask import Flask
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://your-key@bugsink.yourcompany.com/1",
    integrations=[
        FlaskIntegration(
            transaction_style="url",
        ),
    ],
    traces_sample_rate=0.1,
)

app = Flask(__name__)
```

---

### FastAPI

```python
from fastapi import FastAPI
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

sentry_sdk.init(
    dsn="https://your-key@bugsink.yourcompany.com/1",
    integrations=[
        StarletteIntegration(
            transaction_style="endpoint",
        ),
        FastApiIntegration(
            transaction_style="endpoint",
        ),
    ],
    traces_sample_rate=0.1,
)

app = FastAPI()
```

---

### Express.js

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

// Must be first middleware
app.use(Sentry.Handlers.requestHandler());
app.use(Sentry.Handlers.tracingHandler());

// Your routes
app.get("/", (req, res) => {
    res.send("Hello World!");
});

// Error handler must be last
app.use(Sentry.Handlers.errorHandler());

app.listen(3000);
```

---

### Fastify

```javascript
const fastify = require("fastify")();
const Sentry = require("@sentry/node");

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    integrations: [
        new Sentry.Integrations.Http({ tracing: true }),
    ],
    tracesSampleRate: 0.1,
});

fastify.addHook("onError", async (request, reply, error) => {
    Sentry.captureException(error);
});

fastify.listen({ port: 3000 });
```

---

### NestJS

```typescript
// main.ts
import * as Sentry from "@sentry/node";
import { NestFactory } from "@nestjs/core";
import { AppModule } from "./app.module";

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    tracesSampleRate: 0.1,
});

async function bootstrap() {
    const app = await NestFactory.create(AppModule);
    await app.listen(3000);
}

bootstrap();
```

```typescript
// sentry.interceptor.ts
import { CallHandler, ExecutionContext, Injectable, NestInterceptor } from "@nestjs/common";
import * as Sentry from "@sentry/node";
import { Observable, tap } from "rxjs";

@Injectable()
export class SentryInterceptor implements NestInterceptor {
    intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
        return next.handle().pipe(
            tap({
                error: (exception) => {
                    Sentry.captureException(exception);
                },
            })
        );
    }
}
```

---

### Laravel

#### Installation

```bash
composer require sentry/sentry-laravel
php artisan sentry:publish --dsn=https://your-key@bugsink.yourcompany.com/1
```

#### Configuration

```php
// config/sentry.php
return [
    'dsn' => env('SENTRY_LARAVEL_DSN', 'https://your-key@bugsink.yourcompany.com/1'),
    'release' => env('SENTRY_RELEASE'),
    'environment' => env('APP_ENV', 'production'),
    'traces_sample_rate' => 0.1,
    'send_default_pii' => true,
];
```

#### Usage

```php
// Report exception
try {
    $this->processOrder($order);
} catch (\Exception $e) {
    \Sentry\captureException($e);
    throw $e;
}

// Add context
\Sentry\configureScope(function (\Sentry\State\Scope $scope): void {
    $scope->setUser(['id' => auth()->id()]);
    $scope->setTag('feature', 'checkout');
});
```

---

### Symfony

#### Installation

```bash
composer require sentry/sentry-symfony
```

#### Configuration

```yaml
# config/packages/sentry.yaml
sentry:
    dsn: '%env(SENTRY_DSN)%'
    options:
        environment: '%kernel.environment%'
        release: '%env(APP_VERSION)%'
        traces_sample_rate: 0.1
```

---

### Rails

#### Installation

```ruby
# Gemfile
gem "sentry-ruby"
gem "sentry-rails"
```

#### Configuration

```ruby
# config/initializers/sentry.rb
Sentry.init do |config|
    config.dsn = "https://your-key@bugsink.yourcompany.com/1"
    config.environment = Rails.env
    config.release = "myapp@#{MyApp::VERSION}"
    config.traces_sample_rate = 0.1
    config.breadcrumbs_logger = [:active_support_logger, :http_logger]

    # Capture user info
    config.send_default_pii = true
end
```

---

### Spring Boot

#### Installation

```xml
<dependency>
    <groupId>io.sentry</groupId>
    <artifactId>sentry-spring-boot-starter-jakarta</artifactId>
    <version>7.+</version>
</dependency>
```

#### Configuration

```yaml
# application.yml
sentry:
  dsn: https://your-key@bugsink.yourcompany.com/1
  environment: ${SPRING_PROFILES_ACTIVE:production}
  release: ${APP_VERSION:unknown}
  traces-sample-rate: 0.1
  exception-resolver-order: -2147483647
```

---

### ASP.NET Core

#### Installation

```bash
dotnet add package Sentry.AspNetCore
```

#### Configuration

```csharp
// Program.cs
var builder = WebApplication.CreateBuilder(args);

builder.WebHost.UseSentry(options =>
{
    options.Dsn = "https://your-key@bugsink.yourcompany.com/1";
    options.Environment = builder.Environment.EnvironmentName;
    options.Release = "myapp@1.2.3";
    options.TracesSampleRate = 0.1;
    options.SendDefaultPii = true;
});

var app = builder.Build();

app.UseSentryTracing();

app.Run();
```

---

### Gin (Go)

```go
package main

import (
    "github.com/getsentry/sentry-go"
    sentrygin "github.com/getsentry/sentry-go/gin"
    "github.com/gin-gonic/gin"
)

func main() {
    sentry.Init(sentry.ClientOptions{
        Dsn:              "https://your-key@bugsink.yourcompany.com/1",
        TracesSampleRate: 0.1,
    })

    r := gin.Default()
    r.Use(sentrygin.New(sentrygin.Options{
        Repanic: true,
    }))

    r.GET("/", func(c *gin.Context) {
        c.String(200, "Hello World!")
    })

    r.Run(":8080")
}
```

---

### Echo (Go)

```go
package main

import (
    "github.com/getsentry/sentry-go"
    sentryecho "github.com/getsentry/sentry-go/echo"
    "github.com/labstack/echo/v4"
)

func main() {
    sentry.Init(sentry.ClientOptions{
        Dsn:              "https://your-key@bugsink.yourcompany.com/1",
        TracesSampleRate: 0.1,
    })

    e := echo.New()
    e.Use(sentryecho.New(sentryecho.Options{
        Repanic: true,
    }))

    e.GET("/", func(c echo.Context) error {
        return c.String(200, "Hello World!")
    })

    e.Start(":8080")
}
```

---

## Serverless

### AWS Lambda

#### Python

```python
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

sentry_sdk.init(
    dsn="https://your-key@bugsink.yourcompany.com/1",
    integrations=[AwsLambdaIntegration(timeout_warning=True)],
    traces_sample_rate=0.1,
)

def handler(event, context):
    # Your function code
    return {"statusCode": 200}
```

#### Node.js

```javascript
const Sentry = require("@sentry/aws-serverless");

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    tracesSampleRate: 0.1,
});

exports.handler = Sentry.wrapHandler(async (event, context) => {
    // Your function code
    return { statusCode: 200 };
});
```

---

### Google Cloud Functions

```python
import sentry_sdk
from sentry_sdk.integrations.gcp import GcpIntegration

sentry_sdk.init(
    dsn="https://your-key@bugsink.yourcompany.com/1",
    integrations=[GcpIntegration(timeout_warning=True)],
    traces_sample_rate=0.1,
)

def hello_http(request):
    return "Hello World!"
```

---

### Azure Functions

```python
import sentry_sdk
from sentry_sdk.integrations.serverless import serverless_function

sentry_sdk.init(
    dsn="https://your-key@bugsink.yourcompany.com/1",
    traces_sample_rate=0.1,
)

@serverless_function
def main(req):
    return "Hello World!"
```

---

### Vercel

Use the Next.js SDK with Vercel's environment variables:

```javascript
// sentry.client.config.js
import * as Sentry from "@sentry/nextjs";

Sentry.init({
    dsn: "https://your-key@bugsink.yourcompany.com/1",
    environment: process.env.VERCEL_ENV,
    release: process.env.VERCEL_GIT_COMMIT_SHA,
});
```

---

### Cloudflare Workers

```javascript
import * as Sentry from "@sentry/cloudflare";

export default {
    async fetch(request, env, ctx) {
        Sentry.init({
            dsn: "https://your-key@bugsink.yourcompany.com/1",
        });

        try {
            return await handleRequest(request);
        } catch (error) {
            Sentry.captureException(error);
            throw error;
        }
    },
};
```

---

## Configuration Options

### Common Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `dsn` | string | - | Data Source Name (required) |
| `environment` | string | - | Environment name (production, staging, etc.) |
| `release` | string | - | Application version |
| `sample_rate` / `sampleRate` | float | 1.0 | Error event sample rate (0.0-1.0) |
| `traces_sample_rate` / `tracesSampleRate` | float | 0.0 | Performance trace sample rate |
| `debug` | bool | false | Enable SDK debug logging |
| `max_breadcrumbs` / `maxBreadcrumbs` | int | 100 | Maximum breadcrumbs to keep |
| `attach_stacktrace` / `attachStacktrace` | bool | true | Attach stack traces to messages |
| `send_default_pii` / `sendDefaultPii` | bool | false | Include PII in events |

### Hooks

| Hook | Description |
|------|-------------|
| `before_send` / `beforeSend` | Modify or filter events before sending |
| `before_send_transaction` / `beforeSendTransaction` | Modify or filter transactions |
| `before_breadcrumb` / `beforeBreadcrumb` | Modify or filter breadcrumbs |

---

## Best Practices

### 1. Always Set Environment and Release

```python
sentry_sdk.init(
    dsn="...",
    environment=os.getenv("APP_ENV", "production"),
    release=f"myapp@{version}",
)
```

### 2. Use Appropriate Sample Rates

- **Errors:** Keep at 1.0 (100%) - you want all errors
- **Traces:** Start at 0.1 (10%) and adjust based on volume
- **Replays:** Start at 0.1 for sessions, 1.0 for errors

### 3. Add Meaningful Context

```python
sentry_sdk.set_user({"id": user.id, "email": user.email})
sentry_sdk.set_tag("feature", "checkout")
sentry_sdk.set_context("order", {"id": order.id, "total": order.total})
```

### 4. Use Breadcrumbs for Debugging

```python
sentry_sdk.add_breadcrumb(
    category="payment",
    message=f"Processing payment for order {order_id}",
    level="info",
)
```

### 5. Filter Sensitive Data

```python
def before_send(event, hint):
    # Remove sensitive headers
    if "request" in event:
        headers = event["request"].get("headers", {})
        for key in ["Authorization", "Cookie", "X-API-Key"]:
            if key in headers:
                headers[key] = "[Filtered]"
    return event
```

### 6. Handle Shutdown Gracefully

```python
import atexit
import sentry_sdk

atexit.register(lambda: sentry_sdk.flush(timeout=2.0))
```

### 7. Test Your Integration

```python
# Verify SDK is working
sentry_sdk.capture_message("Test message from Bugsink integration")
```

---

## Further Reading

- [Bugsink Quick Start](quickstart.md)
- [Bugsink Configuration](configuration.md)
- [Official Sentry Documentation](https://docs.sentry.io/)
