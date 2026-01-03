//! Bugsink/Sentry SDK Integration Example for Rust
//! ================================================
//!
//! This example demonstrates comprehensive error tracking integration
//! using the Sentry SDK with a self-hosted Bugsink server.
//!
//! Requirements (Cargo.toml):
//!     [dependencies]
//!     sentry = "0.32"
//!     sentry-tracing = "0.32"
//!     tracing = "0.1"
//!     tracing-subscriber = "0.3"
//!     tokio = { version = "1", features = ["full"] }
//!     anyhow = "1.0"
//!     thiserror = "1.0"
//!
//! DSN Format:
//!     https://<project-key>@<your-bugsink-host>/<project-id>

use sentry::{
    integrations::tracing::EventFilter,
    protocol::{Breadcrumb, Event, User, Value},
    ClientOptions, Hub, Level, Scope, TransactionContext,
};
use std::{
    collections::BTreeMap,
    env,
    sync::Arc,
    time::{Duration, Instant},
};
use tracing::{info, instrument, warn};

// =============================================================================
// CONFIGURATION
// =============================================================================

mod config {
    use std::env;

    pub fn dsn() -> String {
        env::var("SENTRY_DSN").unwrap_or_else(|_| {
            "https://your-project-key@errors.observability.app.bauer-group.com/1".to_string()
        })
    }

    pub fn environment() -> String {
        env::var("ENVIRONMENT").unwrap_or_else(|_| "development".to_string())
    }

    pub fn release() -> String {
        env::var("APP_VERSION").unwrap_or_else(|_| "1.0.0".to_string())
    }

    pub fn is_production() -> bool {
        environment() == "production"
    }
}

// =============================================================================
// CUSTOM ERRORS
// =============================================================================

#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("Business logic error: {0}")]
    BusinessError(String),

    #[error("Database error: {0}")]
    DatabaseError(String),

    #[error("External service error: {0}")]
    ExternalServiceError(String),

    #[error("Validation error: {0}")]
    ValidationError(String),
}

/// Expected business error that should not be reported to Sentry
#[derive(Debug, thiserror::Error)]
#[error("Expected business error: {0}")]
pub struct ExpectedBusinessError(pub String);

// =============================================================================
// SENTRY SERVICE
// =============================================================================

/// Service for Sentry operations.
/// Provides comprehensive error tracking and performance monitoring.
pub struct SentryService {
    _guard: Option<sentry::ClientInitGuard>,
}

impl SentryService {
    /// Create and initialize a new SentryService.
    pub fn new() -> Self {
        let guard = Self::init_sentry();
        Self { _guard: guard }
    }

    /// Initialize Sentry SDK.
    fn init_sentry() -> Option<sentry::ClientInitGuard> {
        let dsn = config::dsn();
        if dsn.is_empty() || dsn.contains("your-project-key") {
            println!("Sentry DSN not configured, running without error tracking");
            return None;
        }

        let traces_sample_rate = if config::is_production() { 0.1 } else { 1.0 };

        let guard = sentry::init((
            dsn,
            ClientOptions {
                release: Some(format!("my-app@{}", config::release()).into()),
                environment: Some(config::environment().into()),
                debug: !config::is_production(),
                attach_stacktrace: true,
                send_default_pii: false,
                max_breadcrumbs: 50,
                traces_sample_rate,
                before_send: Some(Arc::new(before_send_handler)),
                before_breadcrumb: Some(Arc::new(before_breadcrumb_handler)),
                ..Default::default()
            },
        ));

        // Set global tags
        sentry::configure_scope(|scope| {
            scope.set_tag("app.component", "backend");
            scope.set_tag("app.runtime", "rust");
            scope.set_tag("app.rust_version", env!("CARGO_PKG_RUST_VERSION"));
        });

        println!("Sentry initialized for environment: {}", config::environment());

        Some(guard)
    }

    /// Set user context.
    pub fn set_user(&self, id: &str, email: Option<&str>, username: Option<&str>, ip_address: Option<&str>) {
        sentry::configure_scope(|scope| {
            scope.set_user(Some(User {
                id: Some(id.to_string()),
                email: email.map(String::from),
                username: username.map(String::from),
                ip_address: ip_address.map(String::from),
                ..Default::default()
            }));
        });
    }

    /// Set user with additional data.
    pub fn set_user_with_data(
        &self,
        id: &str,
        email: Option<&str>,
        username: Option<&str>,
        ip_address: Option<&str>,
        data: BTreeMap<String, Value>,
    ) {
        sentry::configure_scope(|scope| {
            scope.set_user(Some(User {
                id: Some(id.to_string()),
                email: email.map(String::from),
                username: username.map(String::from),
                ip_address: ip_address.map(String::from),
                data,
                ..Default::default()
            }));
        });
    }

    /// Clear user context.
    pub fn clear_user(&self) {
        sentry::configure_scope(|scope| {
            scope.set_user(None);
        });
    }

    /// Add a breadcrumb.
    pub fn add_breadcrumb(&self, message: &str, category: &str, level: Level, data: Option<BTreeMap<String, Value>>) {
        sentry::add_breadcrumb(Breadcrumb {
            message: Some(message.to_string()),
            category: Some(category.to_string()),
            level,
            data: data.unwrap_or_default(),
            ..Default::default()
        });
    }

    /// Set a tag.
    pub fn set_tag(&self, key: &str, value: &str) {
        sentry::configure_scope(|scope| {
            scope.set_tag(key, value);
        });
    }

    /// Set extra context.
    pub fn set_extra<V: Into<Value>>(&self, key: &str, value: V) {
        sentry::configure_scope(|scope| {
            scope.set_extra(key, value.into());
        });
    }

    /// Set custom context.
    pub fn set_context(&self, name: &str, context: BTreeMap<String, Value>) {
        sentry::configure_scope(|scope| {
            scope.set_context(name, sentry::protocol::Context::Other(context));
        });
    }

    /// Capture an error.
    pub fn capture_error<E: std::error::Error + ?Sized>(&self, error: &E) -> sentry::protocol::Uuid {
        sentry::capture_error(error)
    }

    /// Capture an error with extra context.
    pub fn capture_error_with_context<E: std::error::Error + ?Sized>(
        &self,
        error: &E,
        extra_context: BTreeMap<String, Value>,
    ) -> sentry::protocol::Uuid {
        sentry::with_scope(
            |scope| {
                for (key, value) in extra_context {
                    scope.set_extra(&key, value);
                }
            },
            || sentry::capture_error(error),
        )
    }

    /// Capture a message.
    pub fn capture_message(&self, message: &str, level: Level) -> sentry::protocol::Uuid {
        sentry::capture_message(message, level)
    }

    /// Capture a message with extra context.
    pub fn capture_message_with_context(
        &self,
        message: &str,
        level: Level,
        extra_context: BTreeMap<String, Value>,
    ) -> sentry::protocol::Uuid {
        sentry::with_scope(
            |scope| {
                for (key, value) in extra_context {
                    scope.set_extra(&key, value);
                }
            },
            || sentry::capture_message(message, level),
        )
    }

    /// Execute a closure within a transaction.
    pub fn with_transaction<F, R>(&self, name: &str, op: &str, f: F) -> R
    where
        F: FnOnce(&sentry::TransactionOrSpan) -> R,
    {
        let ctx = TransactionContext::new(name, op);
        let transaction = sentry::start_transaction(ctx);

        // Bind transaction to scope
        sentry::configure_scope(|scope| {
            scope.set_span(Some(transaction.clone().into()));
        });

        let result = f(&transaction.clone().into());

        transaction.finish();
        result
    }

    /// Execute a closure within a child span.
    pub fn with_span<F, R>(&self, parent: &sentry::TransactionOrSpan, op: &str, description: &str, f: F) -> R
    where
        F: FnOnce(&sentry::Span) -> R,
    {
        let span = parent.start_child(op, description);
        let result = f(&span);
        span.finish();
        result
    }

    /// Execute a closure within a scope.
    pub fn with_scope<C, F, R>(&self, configure: C, f: F) -> R
    where
        C: FnOnce(&mut Scope),
        F: FnOnce() -> R,
    {
        sentry::with_scope(configure, f)
    }
}

impl Default for SentryService {
    fn default() -> Self {
        Self::new()
    }
}

// =============================================================================
// HOOKS
// =============================================================================

/// Process events before sending.
fn before_send_handler(mut event: Event<'static>) -> Option<Event<'static>> {
    // Sanitize sensitive headers
    if let Some(ref mut request) = event.request {
        if let Some(ref mut headers) = request.headers {
            let sensitive_headers = ["Authorization", "Cookie", "X-API-Key"];
            for header in sensitive_headers {
                if headers.contains_key(header) {
                    headers.insert(header.to_string(), "[REDACTED]".to_string());
                }
            }
        }
    }

    // Filter specific exceptions (check exception type in message)
    if let Some(ref exception) = event.exception {
        for exc in &exception.values {
            if exc.ty.as_deref() == Some("ExpectedBusinessError") {
                return None; // Don't send this event
            }
        }
    }

    Some(event)
}

/// Process breadcrumbs before adding.
fn before_breadcrumb_handler(breadcrumb: Breadcrumb) -> Option<Breadcrumb> {
    // Filter health check requests
    if breadcrumb.category.as_deref() == Some("http") {
        if let Some(url) = breadcrumb.data.get("url") {
            if url.as_str().map(|s| s.contains("/health")).unwrap_or(false) {
                return None;
            }
        }
    }

    Some(breadcrumb)
}

// =============================================================================
// EXAMPLE SERVICE
// =============================================================================

/// Example service demonstrating Sentry integration patterns.
pub struct ExampleService {
    sentry: Arc<SentryService>,
}

impl ExampleService {
    pub fn new(sentry: Arc<SentryService>) -> Self {
        Self { sentry }
    }

    /// Example method with error tracking.
    #[instrument(skip(self))]
    pub fn fetch_data(&self, id: &str) -> Result<String, AppError> {
        self.sentry.add_breadcrumb(
            &format!("Fetching data for {}", id),
            "service",
            Level::Info,
            Some({
                let mut data = BTreeMap::new();
                data.insert("id".to_string(), Value::from(id));
                data
            }),
        );

        if id == "error" {
            return Err(AppError::DatabaseError("Failed to fetch data".to_string()));
        }

        Ok(format!("Data for {}", id))
    }

    /// Example method with transaction tracking.
    pub fn process_batch(&self, items: &[&str]) -> usize {
        self.sentry.with_transaction("process_batch", "task", |transaction| {
            let mut processed = 0;

            for item in items {
                self.sentry.with_span(
                    transaction,
                    "task.item",
                    &format!("process_{}", item),
                    |_span| {
                        std::thread::sleep(Duration::from_millis(50)); // Simulate work
                        processed += 1;
                    },
                );
            }

            processed
        })
    }

    /// Async example method.
    #[instrument(skip(self))]
    pub async fn async_operation(&self, input: &str) -> Result<String, AppError> {
        self.sentry.add_breadcrumb(
            &format!("Processing async operation for {}", input),
            "async",
            Level::Info,
            None,
        );

        tokio::time::sleep(Duration::from_millis(100)).await;

        Ok(format!("Processed: {}", input))
    }
}

// =============================================================================
// ACTIX-WEB INTEGRATION EXAMPLE
// =============================================================================

/*
// main.rs with Actix-Web

use actix_web::{web, App, HttpRequest, HttpResponse, HttpServer, middleware};
use sentry_actix::Sentry;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Initialize Sentry
    let _guard = sentry::init((
        std::env::var("SENTRY_DSN").unwrap(),
        sentry::ClientOptions {
            release: Some("my-app@1.0.0".into()),
            ..Default::default()
        },
    ));

    HttpServer::new(|| {
        App::new()
            // Add Sentry middleware
            .wrap(Sentry::new())
            .route("/", web::get().to(index))
            .route("/api/users/{id}", web::get().to(get_user))
            .route("/api/error", web::get().to(trigger_error))
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}

async fn index() -> HttpResponse {
    sentry::add_breadcrumb(sentry::Breadcrumb {
        message: Some("Homepage visited".to_string()),
        category: Some("navigation".to_string()),
        ..Default::default()
    });

    HttpResponse::Ok().json(serde_json::json!({ "status": "ok" }))
}

async fn get_user(path: web::Path<String>) -> HttpResponse {
    let user_id = path.into_inner();

    sentry::add_breadcrumb(sentry::Breadcrumb {
        message: Some(format!("Fetching user {}", user_id)),
        category: Some("api".to_string()),
        ..Default::default()
    });

    if user_id == "0" {
        return HttpResponse::BadRequest().json(serde_json::json!({
            "error": "Invalid user ID"
        }));
    }

    HttpResponse::Ok().json(serde_json::json!({
        "user_id": user_id,
        "name": "Test User"
    }))
}

async fn trigger_error() -> HttpResponse {
    // This will be captured by Sentry
    panic!("Test error from /api/error endpoint");
}
*/

// =============================================================================
// AXUM INTEGRATION EXAMPLE
// =============================================================================

/*
// main.rs with Axum

use axum::{
    extract::Path,
    http::StatusCode,
    routing::get,
    Json, Router,
};
use sentry::integrations::tower::{NewSentryLayer, SentryHttpLayer};
use tower::ServiceBuilder;

#[tokio::main]
async fn main() {
    // Initialize Sentry
    let _guard = sentry::init((
        std::env::var("SENTRY_DSN").unwrap(),
        sentry::ClientOptions {
            release: Some("my-app@1.0.0".into()),
            traces_sample_rate: 0.5,
            ..Default::default()
        },
    ));

    let app = Router::new()
        .route("/", get(index))
        .route("/api/users/:id", get(get_user))
        .layer(
            ServiceBuilder::new()
                .layer(NewSentryLayer::new_from_top())
                .layer(SentryHttpLayer::with_transaction()),
        );

    let listener = tokio::net::TcpListener::bind("127.0.0.1:8080").await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn index() -> Json<serde_json::Value> {
    sentry::add_breadcrumb(sentry::Breadcrumb {
        message: Some("Homepage visited".to_string()),
        category: Some("navigation".to_string()),
        ..Default::default()
    });

    Json(serde_json::json!({ "status": "ok" }))
}

async fn get_user(Path(user_id): Path<String>) -> Result<Json<serde_json::Value>, StatusCode> {
    sentry::add_breadcrumb(sentry::Breadcrumb {
        message: Some(format!("Fetching user {}", user_id)),
        category: Some("api".to_string()),
        ..Default::default()
    });

    if user_id == "0" {
        return Err(StatusCode::BAD_REQUEST);
    }

    Ok(Json(serde_json::json!({
        "user_id": user_id,
        "name": "Test User"
    })))
}
*/

// =============================================================================
// MAIN EXAMPLE
// =============================================================================

fn main() {
    println!("{}", "=".repeat(60));
    println!("Bugsink/Sentry Rust SDK Integration Example");
    println!("{}", "=".repeat(60));

    // Initialize Sentry service
    let sentry = Arc::new(SentryService::new());

    // Set user context
    let mut user_data = BTreeMap::new();
    user_data.insert("subscription_tier".to_string(), Value::from("premium"));

    sentry.set_user_with_data(
        "user-123",
        Some("developer@example.com"),
        Some("developer"),
        Some("127.0.0.1"),
        user_data,
    );

    // Add breadcrumbs
    sentry.add_breadcrumb("Application started", "app", Level::Info, None);
    sentry.add_breadcrumb("User authenticated", "auth", Level::Info, None);

    // Example 1: Capture handled exception
    println!("\n1. Capturing handled exception...");
    let error = AppError::DatabaseError("Connection refused".to_string());
    let mut context = BTreeMap::new();
    context.insert("operation".to_string(), Value::from("database_connect"));
    context.insert("host".to_string(), Value::from("localhost:5432"));

    let event_id = sentry.capture_error_with_context(&error, context);
    println!("   Exception captured: {}", event_id);

    // Example 2: Capture message
    println!("\n2. Capturing info message...");
    let mut msg_context = BTreeMap::new();
    msg_context.insert("steps_completed".to_string(), Value::from(5));
    msg_context.insert("time_taken_seconds".to_string(), Value::from(120));

    let event_id = sentry.capture_message_with_context(
        "User completed onboarding flow",
        Level::Info,
        msg_context,
    );
    println!("   Message captured: {}", event_id);

    // Example 3: Use example service
    println!("\n3. Using example service...");
    let service = ExampleService::new(Arc::clone(&sentry));
    match service.fetch_data("123") {
        Ok(data) => println!("   Data fetched: {}", data),
        Err(e) => {
            sentry.capture_error(&e);
            println!("   Error handled");
        }
    }

    // Example 4: Transaction with service
    println!("\n4. Processing batch with transaction...");
    let processed = service.process_batch(&["a", "b", "c"]);
    println!("   Processed {} items", processed);

    // Example 5: Scoped context
    println!("\n5. Using scoped context...");
    sentry.with_scope(
        |scope| {
            scope.set_tag("feature", "new_checkout");
            scope.set_extra("cart_items", Value::from(3));
            scope.set_extra("total_amount", Value::from(99.99));
        },
        || {
            sentry::capture_message("Checkout initiated", Level::Info);
        },
    );
    println!("   Scoped message captured");

    // Example 6: Manual transaction with spans
    println!("\n6. Creating transaction with spans...");
    sentry.with_transaction("order_processing", "task", |transaction| {
        sentry.with_span(transaction, "db.query", "Fetch order", |_| {
            std::thread::sleep(Duration::from_millis(50));
        });

        sentry.with_span(transaction, "http.client", "Payment API", |_| {
            std::thread::sleep(Duration::from_millis(100));
        });

        sentry.with_span(transaction, "db.query", "Update order status", |_| {
            std::thread::sleep(Duration::from_millis(50));
        });
    });
    println!("   Transaction with spans recorded");

    // Clean up
    sentry.clear_user();

    println!("\n{}", "=".repeat(60));
    println!("All examples completed!");
    println!("Check your Bugsink dashboard");
    println!("{}", "=".repeat(60));

    // Events are flushed automatically when _guard is dropped
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_example_service_fetch_data() {
        let sentry = Arc::new(SentryService::new());
        let service = ExampleService::new(sentry);

        let result = service.fetch_data("123");
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), "Data for 123");

        let error_result = service.fetch_data("error");
        assert!(error_result.is_err());
    }

    #[test]
    fn test_example_service_process_batch() {
        let sentry = Arc::new(SentryService::new());
        let service = ExampleService::new(sentry);

        let processed = service.process_batch(&["a", "b", "c"]);
        assert_eq!(processed, 3);
    }
}
