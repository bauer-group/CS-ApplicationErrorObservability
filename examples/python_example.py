#!/usr/bin/env python3
"""
Bugsink/Sentry SDK Integration Example for Python
==================================================

This example demonstrates comprehensive error tracking integration
using the Sentry SDK with a self-hosted Bugsink server.

Requirements:
    pip install sentry-sdk flask requests

DSN Format:
    https://<project-key>@<your-bugsink-host>/<project-id>
"""

import os
import sys
import logging
from datetime import datetime
from functools import wraps

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration

# =============================================================================
# CONFIGURATION
# =============================================================================

# Get DSN from environment variable or use placeholder
SENTRY_DSN = os.getenv(
    "SENTRY_DSN",
    "https://your-project-key@errors.observability.app.bauer-group.com/1"
)

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
RELEASE = os.getenv("APP_VERSION", "1.0.0")
SERVER_NAME = os.getenv("HOSTNAME", "unknown")


# =============================================================================
# SENTRY INITIALIZATION
# =============================================================================

def init_sentry():
    """
    Initialize Sentry SDK with comprehensive configuration.
    Call this once at application startup.
    """

    # Configure logging integration
    logging_integration = LoggingIntegration(
        level=logging.INFO,        # Capture INFO and above as breadcrumbs
        event_level=logging.ERROR  # Send ERROR and above as events
    )

    sentry_sdk.init(
        dsn=SENTRY_DSN,

        # Environment & Release
        environment=ENVIRONMENT,
        release=f"my-app@{RELEASE}",
        server_name=SERVER_NAME,

        # Integrations
        integrations=[
            logging_integration,
            ThreadingIntegration(propagate_hub=True),
        ],

        # Performance Monitoring
        traces_sample_rate=1.0,  # 100% in dev, reduce in production (e.g., 0.1)
        profiles_sample_rate=0.1,  # Profile 10% of transactions

        # Error Sampling
        sample_rate=1.0,  # Send 100% of errors

        # Data Handling
        send_default_pii=False,  # Don't send PII by default
        max_breadcrumbs=50,
        attach_stacktrace=True,

        # Request Data
        max_request_body_size="medium",  # "small", "medium", "always", "never"

        # Before Send Hook - sanitize/filter events
        before_send=before_send_handler,

        # Before Breadcrumb Hook
        before_breadcrumb=before_breadcrumb_handler,

        # Debug mode (disable in production)
        debug=ENVIRONMENT == "development",
    )

    # Set global tags
    sentry_sdk.set_tag("app.component", "backend")
    sentry_sdk.set_tag("app.team", "platform")

    print(f"Sentry initialized for environment: {ENVIRONMENT}")


def before_send_handler(event, hint):
    """
    Process events before sending to Sentry.
    Use this to sanitize sensitive data or filter events.
    """
    # Example: Remove sensitive headers
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        sensitive_headers = ["Authorization", "Cookie", "X-API-Key"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[REDACTED]"

    # Example: Filter out specific exceptions
    if "exception" in event:
        for exception in event["exception"].get("values", []):
            # Don't send expected/handled exceptions
            if exception.get("type") == "ExpectedBusinessException":
                return None

    # Example: Add custom fingerprint for grouping
    if "exception" in event:
        exc_type = event["exception"]["values"][0].get("type", "")
        if exc_type == "DatabaseConnectionError":
            event["fingerprint"] = ["database-connection-error"]

    return event


def before_breadcrumb_handler(breadcrumb, hint):
    """
    Process breadcrumbs before adding to the event.
    Use this to filter or sanitize breadcrumb data.
    """
    # Filter out noisy breadcrumbs
    if breadcrumb.get("category") == "httplib" and "/health" in breadcrumb.get("data", {}).get("url", ""):
        return None

    # Sanitize SQL queries
    if breadcrumb.get("category") == "query":
        message = breadcrumb.get("message", "")
        if "password" in message.lower():
            breadcrumb["message"] = "[QUERY REDACTED - CONTAINS SENSITIVE DATA]"

    return breadcrumb


# =============================================================================
# CONTEXT MANAGEMENT
# =============================================================================

def set_user_context(user_id: str, email: str = None, username: str = None,
                     ip_address: str = None, **extra):
    """
    Set user context for error tracking.
    Call this after user authentication.
    """
    user_data = {"id": user_id}

    if email:
        user_data["email"] = email
    if username:
        user_data["username"] = username
    if ip_address:
        user_data["ip_address"] = ip_address

    # Add any extra user data
    user_data.update(extra)

    sentry_sdk.set_user(user_data)


def clear_user_context():
    """Clear user context (e.g., on logout)."""
    sentry_sdk.set_user(None)


def add_breadcrumb(message: str, category: str = "custom", level: str = "info",
                   data: dict = None):
    """
    Add a breadcrumb to track user actions/events.
    Breadcrumbs help understand what happened before an error.
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {},
        timestamp=datetime.now()
    )


# =============================================================================
# ERROR CAPTURING
# =============================================================================

def capture_exception(exception: Exception = None, **extra_context):
    """
    Capture an exception with optional extra context.

    Args:
        exception: The exception to capture (or None to capture current)
        **extra_context: Additional context to attach
    """
    with sentry_sdk.push_scope() as scope:
        # Add extra context
        for key, value in extra_context.items():
            scope.set_extra(key, value)

        if exception:
            sentry_sdk.capture_exception(exception)
        else:
            sentry_sdk.capture_exception()


def capture_message(message: str, level: str = "info", **extra_context):
    """
    Capture a message (non-exception event).

    Args:
        message: The message to capture
        level: Severity level (debug, info, warning, error, fatal)
        **extra_context: Additional context to attach
    """
    with sentry_sdk.push_scope() as scope:
        for key, value in extra_context.items():
            scope.set_extra(key, value)

        sentry_sdk.capture_message(message, level=level)


# =============================================================================
# DECORATORS
# =============================================================================

def track_errors(operation_name: str = None):
    """
    Decorator to automatically track errors in a function.

    Usage:
        @track_errors("user_registration")
        def register_user(email, password):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__

            with sentry_sdk.push_scope() as scope:
                scope.set_tag("operation", op_name)
                scope.set_extra("function", func.__name__)
                scope.set_extra("args_count", len(args))

                add_breadcrumb(
                    message=f"Executing {op_name}",
                    category="function",
                    level="info"
                )

                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    scope.set_extra("error_type", type(e).__name__)
                    raise

        return wrapper
    return decorator


def transaction(name: str, op: str = "function"):
    """
    Decorator to create a transaction for performance monitoring.

    Usage:
        @transaction("process_order", op="task")
        def process_order(order_id):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with sentry_sdk.start_transaction(name=name, op=op) as txn:
                try:
                    return func(*args, **kwargs)
                except Exception:
                    txn.set_status("internal_error")
                    raise
                else:
                    txn.set_status("ok")

        return wrapper
    return decorator


# =============================================================================
# FLASK INTEGRATION EXAMPLE
# =============================================================================

def create_flask_app():
    """
    Example Flask application with Sentry integration.
    """
    try:
        from flask import Flask, request, g
        from sentry_sdk.integrations.flask import FlaskIntegration
    except ImportError:
        print("Flask not installed. Run: pip install flask")
        return None

    # Re-initialize with Flask integration
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
        release=f"my-app@{RELEASE}",
        integrations=[
            FlaskIntegration(
                transaction_style="url",  # or "endpoint"
            ),
        ],
        traces_sample_rate=0.5,
        before_send=before_send_handler,
    )

    app = Flask(__name__)

    @app.before_request
    def before_request():
        """Set up request context."""
        g.request_id = request.headers.get("X-Request-ID", "unknown")
        sentry_sdk.set_tag("request_id", g.request_id)

        # Set user context if authenticated
        user_id = request.headers.get("X-User-ID")
        if user_id:
            set_user_context(user_id=user_id)

    @app.route("/")
    def index():
        add_breadcrumb("User visited homepage", category="navigation")
        return {"status": "ok", "message": "Welcome to the API"}

    @app.route("/api/users/<user_id>")
    def get_user(user_id):
        add_breadcrumb(f"Fetching user {user_id}", category="api", data={"user_id": user_id})

        # Simulate user lookup
        if user_id == "0":
            raise ValueError("Invalid user ID")

        return {"user_id": user_id, "name": "Test User"}

    @app.route("/api/error")
    def trigger_error():
        """Endpoint to test error tracking."""
        division_by_zero = 1 / 0
        return {"result": division_by_zero}

    @app.route("/api/message")
    def send_message():
        """Endpoint to test message capture."""
        capture_message(
            "User triggered test message",
            level="info",
            endpoint="/api/message",
            custom_data={"test": True}
        )
        return {"status": "message sent"}

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Global exception handler."""
        # Sentry captures this automatically with FlaskIntegration
        # but we can add extra context
        sentry_sdk.set_context("error_details", {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "endpoint": request.endpoint,
        })

        return {"error": str(e)}, 500

    return app


# =============================================================================
# ASYNC SUPPORT (Python 3.7+)
# =============================================================================

async def async_capture_example():
    """
    Example of capturing errors in async code.
    """
    import asyncio

    async def async_task_that_fails():
        await asyncio.sleep(0.1)
        raise RuntimeError("Async task failed")

    try:
        await async_task_that_fails()
    except Exception as e:
        capture_exception(e, task="async_example", async_context=True)


# =============================================================================
# MAIN EXAMPLE
# =============================================================================

def main():
    """
    Demonstration of all Sentry integration features.
    """
    print("=" * 60)
    print("Bugsink/Sentry Python SDK Integration Example")
    print("=" * 60)

    # Initialize Sentry
    init_sentry()

    # Set user context
    set_user_context(
        user_id="user-123",
        email="developer@example.com",
        username="developer",
        subscription_tier="premium"
    )

    # Add breadcrumbs to track user journey
    add_breadcrumb("Application started", category="app", level="info")
    add_breadcrumb("User authenticated", category="auth", level="info")
    add_breadcrumb("Loading dashboard", category="navigation", level="info")

    # Example 1: Capture a handled exception
    print("\n1. Capturing handled exception...")
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        capture_exception(
            e,
            operation="division_example",
            numerator=10,
            denominator=0
        )
        print("   Exception captured and sent to Bugsink")

    # Example 2: Capture a message
    print("\n2. Capturing info message...")
    capture_message(
        "User completed onboarding flow",
        level="info",
        steps_completed=5,
        time_taken_seconds=120
    )
    print("   Message captured and sent to Bugsink")

    # Example 3: Use decorator for automatic tracking
    print("\n3. Using @track_errors decorator...")

    @track_errors("data_processing")
    def process_data(data):
        if not data:
            raise ValueError("Data cannot be empty")
        return len(data)

    try:
        process_data([])
    except ValueError:
        print("   Error tracked automatically via decorator")

    # Example 4: Transaction for performance monitoring
    print("\n4. Creating performance transaction...")

    @transaction("batch_operation", op="task")
    def batch_operation():
        import time
        time.sleep(0.1)  # Simulate work
        return "completed"

    batch_operation()
    print("   Transaction recorded")

    # Example 5: Scoped context
    print("\n5. Using scoped context...")
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("feature", "new_checkout")
        scope.set_extra("cart_items", 3)
        scope.set_extra("total_amount", 99.99)

        capture_message("Checkout initiated", level="info")
    print("   Scoped message captured")

    # Example 6: Manual transaction with spans
    print("\n6. Creating transaction with spans...")
    with sentry_sdk.start_transaction(name="order_processing", op="task") as txn:
        with txn.start_child(op="db.query", description="Fetch order"):
            import time
            time.sleep(0.05)

        with txn.start_child(op="http.client", description="Payment API"):
            time.sleep(0.1)

        with txn.start_child(op="db.query", description="Update order status"):
            time.sleep(0.05)

        txn.set_status("ok")
    print("   Transaction with spans recorded")

    # Clean up
    clear_user_context()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print(f"Check your Bugsink dashboard at: https://{SENTRY_DSN.split('@')[1].split('/')[0]}")
    print("=" * 60)

    # Flush events before exit
    sentry_sdk.flush(timeout=5.0)


if __name__ == "__main__":
    main()
