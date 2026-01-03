/**
 * Bugsink/Sentry SDK Integration Example for Node.js
 * ===================================================
 *
 * This example demonstrates comprehensive error tracking integration
 * using the Sentry SDK with a self-hosted Bugsink server.
 *
 * Requirements:
 *     npm install @sentry/node @sentry/profiling-node express
 *
 * DSN Format:
 *     https://<project-key>@<your-bugsink-host>/<project-id>
 */

const Sentry = require("@sentry/node");
const { nodeProfilingIntegration } = require("@sentry/profiling-node");

// =============================================================================
// CONFIGURATION
// =============================================================================

const SENTRY_DSN =
  process.env.SENTRY_DSN ||
  "https://your-project-key@errors.observability.app.bauer-group.com/1";

const ENVIRONMENT = process.env.NODE_ENV || "development";
const RELEASE = process.env.APP_VERSION || "1.0.0";
const SERVER_NAME = process.env.HOSTNAME || require("os").hostname();

// =============================================================================
// SENTRY INITIALIZATION
// =============================================================================

/**
 * Initialize Sentry SDK with comprehensive configuration.
 * Call this once at application startup, BEFORE any other code.
 */
function initSentry() {
  Sentry.init({
    dsn: SENTRY_DSN,

    // Environment & Release
    environment: ENVIRONMENT,
    release: `my-app@${RELEASE}`,
    serverName: SERVER_NAME,

    // Integrations
    integrations: [
      // Performance Profiling
      nodeProfilingIntegration(),
    ],

    // Performance Monitoring
    tracesSampleRate: ENVIRONMENT === "production" ? 0.1 : 1.0,
    profilesSampleRate: 0.1,

    // Error Sampling
    sampleRate: 1.0,

    // Data Handling
    sendDefaultPii: false,
    maxBreadcrumbs: 50,
    attachStacktrace: true,

    // Request Data
    maxValueLength: 1000,

    // Before Send Hook - sanitize/filter events
    beforeSend: beforeSendHandler,

    // Before Breadcrumb Hook
    beforeBreadcrumb: beforeBreadcrumbHandler,

    // Debug mode
    debug: ENVIRONMENT === "development",
  });

  // Set global tags
  Sentry.setTag("app.component", "backend");
  Sentry.setTag("app.runtime", "nodejs");
  Sentry.setTag("app.version", process.version);

  console.log(`Sentry initialized for environment: ${ENVIRONMENT}`);
}

/**
 * Process events before sending to Sentry.
 * Use this to sanitize sensitive data or filter events.
 */
function beforeSendHandler(event, hint) {
  // Remove sensitive headers
  if (event.request && event.request.headers) {
    const sensitiveHeaders = ["authorization", "cookie", "x-api-key"];
    sensitiveHeaders.forEach((header) => {
      if (event.request.headers[header]) {
        event.request.headers[header] = "[REDACTED]";
      }
    });
  }

  // Filter out specific exceptions
  const exception = hint.originalException;
  if (exception && exception.name === "ExpectedBusinessError") {
    return null; // Don't send this event
  }

  // Add custom fingerprint for specific errors
  if (exception && exception.code === "ECONNREFUSED") {
    event.fingerprint = ["database-connection-error"];
  }

  return event;
}

/**
 * Process breadcrumbs before adding to the event.
 */
function beforeBreadcrumbHandler(breadcrumb, hint) {
  // Filter out health check requests
  if (
    breadcrumb.category === "http" &&
    breadcrumb.data &&
    breadcrumb.data.url &&
    breadcrumb.data.url.includes("/health")
  ) {
    return null;
  }

  // Sanitize sensitive data in breadcrumbs
  if (breadcrumb.data && breadcrumb.data.body) {
    const body = breadcrumb.data.body;
    if (typeof body === "string" && body.includes("password")) {
      breadcrumb.data.body = "[REDACTED]";
    }
  }

  return breadcrumb;
}

// =============================================================================
// CONTEXT MANAGEMENT
// =============================================================================

/**
 * Set user context for error tracking.
 * Call this after user authentication.
 *
 * @param {Object} user - User information
 * @param {string} user.id - User ID (required)
 * @param {string} [user.email] - User email
 * @param {string} [user.username] - Username
 * @param {string} [user.ipAddress] - IP address
 */
function setUserContext(user) {
  Sentry.setUser({
    id: user.id,
    email: user.email,
    username: user.username,
    ip_address: user.ipAddress,
    ...user.extra,
  });
}

/**
 * Clear user context (e.g., on logout).
 */
function clearUserContext() {
  Sentry.setUser(null);
}

/**
 * Add a breadcrumb to track user actions/events.
 *
 * @param {string} message - Breadcrumb message
 * @param {string} [category='custom'] - Category for grouping
 * @param {string} [level='info'] - Severity level
 * @param {Object} [data={}] - Additional data
 */
function addBreadcrumb(message, category = "custom", level = "info", data = {}) {
  Sentry.addBreadcrumb({
    message,
    category,
    level,
    data,
    timestamp: Date.now() / 1000,
  });
}

/**
 * Set custom context for the current scope.
 *
 * @param {string} name - Context name
 * @param {Object} context - Context data
 */
function setContext(name, context) {
  Sentry.setContext(name, context);
}

// =============================================================================
// ERROR CAPTURING
// =============================================================================

/**
 * Capture an exception with optional extra context.
 *
 * @param {Error} error - The error to capture
 * @param {Object} [extraContext={}] - Additional context
 * @returns {string} Event ID
 */
function captureException(error, extraContext = {}) {
  return Sentry.withScope((scope) => {
    Object.entries(extraContext).forEach(([key, value]) => {
      scope.setExtra(key, value);
    });

    return Sentry.captureException(error);
  });
}

/**
 * Capture a message (non-exception event).
 *
 * @param {string} message - The message to capture
 * @param {string} [level='info'] - Severity level
 * @param {Object} [extraContext={}] - Additional context
 * @returns {string} Event ID
 */
function captureMessage(message, level = "info", extraContext = {}) {
  return Sentry.withScope((scope) => {
    Object.entries(extraContext).forEach(([key, value]) => {
      scope.setExtra(key, value);
    });

    return Sentry.captureMessage(message, level);
  });
}

// =============================================================================
// DECORATORS / WRAPPERS
// =============================================================================

/**
 * Wrap a function to automatically track errors.
 *
 * @param {string} operationName - Name of the operation
 * @param {Function} fn - Function to wrap
 * @returns {Function} Wrapped function
 */
function trackErrors(operationName, fn) {
  return function (...args) {
    return Sentry.withScope((scope) => {
      scope.setTag("operation", operationName);
      scope.setExtra("function", fn.name || "anonymous");

      addBreadcrumb(`Executing ${operationName}`, "function", "info");

      try {
        const result = fn.apply(this, args);

        // Handle promises
        if (result && typeof result.then === "function") {
          return result.catch((error) => {
            scope.setExtra("error_type", error.name);
            throw error;
          });
        }

        return result;
      } catch (error) {
        scope.setExtra("error_type", error.name);
        throw error;
      }
    });
  };
}

/**
 * Wrap an async function with a transaction for performance monitoring.
 *
 * @param {string} name - Transaction name
 * @param {string} [op='function'] - Operation type
 * @param {Function} fn - Async function to wrap
 * @returns {Function} Wrapped function
 */
function withTransaction(name, op = "function", fn) {
  return async function (...args) {
    return Sentry.startSpan(
      {
        name,
        op,
      },
      async (span) => {
        try {
          const result = await fn.apply(this, args);
          span.setStatus({ code: 1 }); // OK
          return result;
        } catch (error) {
          span.setStatus({ code: 2, message: error.message }); // ERROR
          throw error;
        }
      }
    );
  };
}

// =============================================================================
// EXPRESS INTEGRATION EXAMPLE
// =============================================================================

/**
 * Create an Express application with Sentry integration.
 */
function createExpressApp() {
  let express;
  try {
    express = require("express");
  } catch (e) {
    console.log("Express not installed. Run: npm install express");
    return null;
  }

  const app = express();

  // Sentry request handler - must be first middleware
  app.use(Sentry.Handlers.requestHandler());

  // Sentry tracing handler
  app.use(Sentry.Handlers.tracingHandler());

  // Parse JSON bodies
  app.use(express.json());

  // Request context middleware
  app.use((req, res, next) => {
    const requestId = req.headers["x-request-id"] || generateRequestId();
    req.requestId = requestId;

    Sentry.setTag("request_id", requestId);

    // Set user context if authenticated
    const userId = req.headers["x-user-id"];
    if (userId) {
      setUserContext({
        id: userId,
        ipAddress: req.ip,
      });
    }

    next();
  });

  // Routes
  app.get("/", (req, res) => {
    addBreadcrumb("User visited homepage", "navigation");
    res.json({ status: "ok", message: "Welcome to the API" });
  });

  app.get("/api/users/:userId", (req, res) => {
    const { userId } = req.params;

    addBreadcrumb(`Fetching user ${userId}`, "api", "info", { userId });

    if (userId === "0") {
      throw new Error("Invalid user ID");
    }

    res.json({ userId, name: "Test User" });
  });

  app.get("/api/error", (req, res) => {
    // This will trigger an error
    throw new Error("Test error from /api/error endpoint");
  });

  app.get("/api/async-error", async (req, res, next) => {
    try {
      await asyncOperationThatFails();
      res.json({ status: "ok" });
    } catch (error) {
      next(error);
    }
  });

  app.get("/api/message", (req, res) => {
    captureMessage("User triggered test message", "info", {
      endpoint: "/api/message",
      customData: { test: true },
    });
    res.json({ status: "message sent" });
  });

  app.post("/api/process", async (req, res, next) => {
    try {
      const result = await Sentry.startSpan(
        { name: "process_data", op: "task" },
        async (span) => {
          // Simulate sub-operations with child spans
          await Sentry.startSpan(
            { name: "validate_input", op: "validation" },
            async () => {
              await sleep(50);
            }
          );

          await Sentry.startSpan(
            { name: "save_to_database", op: "db.query" },
            async () => {
              await sleep(100);
            }
          );

          return { processed: true };
        }
      );

      res.json(result);
    } catch (error) {
      next(error);
    }
  });

  // Sentry error handler - must be before other error handlers
  app.use(Sentry.Handlers.errorHandler());

  // Custom error handler
  app.use((err, req, res, next) => {
    console.error("Error:", err.message);

    res.status(500).json({
      error: err.message,
      requestId: req.requestId,
    });
  });

  return app;
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

function generateRequestId() {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function asyncOperationThatFails() {
  await sleep(100);
  throw new Error("Async operation failed");
}

// =============================================================================
// MAIN EXAMPLE
// =============================================================================

async function main() {
  console.log("=".repeat(60));
  console.log("Bugsink/Sentry Node.js SDK Integration Example");
  console.log("=".repeat(60));

  // Initialize Sentry
  initSentry();

  // Set user context
  setUserContext({
    id: "user-123",
    email: "developer@example.com",
    username: "developer",
    extra: {
      subscriptionTier: "premium",
    },
  });

  // Add breadcrumbs
  addBreadcrumb("Application started", "app", "info");
  addBreadcrumb("User authenticated", "auth", "info");
  addBreadcrumb("Loading dashboard", "navigation", "info");

  // Example 1: Capture a handled exception
  console.log("\n1. Capturing handled exception...");
  try {
    JSON.parse("invalid json");
  } catch (error) {
    const eventId = captureException(error, {
      operation: "json_parsing",
      input: "invalid json",
    });
    console.log(`   Exception captured with event ID: ${eventId}`);
  }

  // Example 2: Capture a message
  console.log("\n2. Capturing info message...");
  const messageId = captureMessage("User completed onboarding flow", "info", {
    stepsCompleted: 5,
    timeTakenSeconds: 120,
  });
  console.log(`   Message captured with event ID: ${messageId}`);

  // Example 3: Use wrapper for automatic tracking
  console.log("\n3. Using trackErrors wrapper...");
  const processData = trackErrors("data_processing", (data) => {
    if (!data || data.length === 0) {
      throw new Error("Data cannot be empty");
    }
    return data.length;
  });

  try {
    processData([]);
  } catch (error) {
    console.log("   Error tracked automatically via wrapper");
  }

  // Example 4: Transaction for performance monitoring
  console.log("\n4. Creating performance transaction...");
  const batchOperation = withTransaction(
    "batch_operation",
    "task",
    async () => {
      await sleep(100);
      return "completed";
    }
  );

  await batchOperation();
  console.log("   Transaction recorded");

  // Example 5: Scoped context
  console.log("\n5. Using scoped context...");
  Sentry.withScope((scope) => {
    scope.setTag("feature", "new_checkout");
    scope.setExtra("cartItems", 3);
    scope.setExtra("totalAmount", 99.99);

    captureMessage("Checkout initiated", "info");
  });
  console.log("   Scoped message captured");

  // Example 6: Transaction with child spans
  console.log("\n6. Creating transaction with spans...");
  await Sentry.startSpan(
    { name: "order_processing", op: "task" },
    async (span) => {
      await Sentry.startSpan(
        { name: "fetch_order", op: "db.query" },
        async () => {
          await sleep(50);
        }
      );

      await Sentry.startSpan(
        { name: "payment_api", op: "http.client" },
        async () => {
          await sleep(100);
        }
      );

      await Sentry.startSpan(
        { name: "update_order_status", op: "db.query" },
        async () => {
          await sleep(50);
        }
      );
    }
  );
  console.log("   Transaction with spans recorded");

  // Clean up
  clearUserContext();

  console.log("\n" + "=".repeat(60));
  console.log("All examples completed!");
  console.log(
    `Check your Bugsink dashboard at: https://${SENTRY_DSN.split("@")[1].split("/")[0]}`
  );
  console.log("=".repeat(60));

  // Flush events before exit
  await Sentry.flush(5000);
}

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}

// Export for use as module
module.exports = {
  initSentry,
  setUserContext,
  clearUserContext,
  addBreadcrumb,
  setContext,
  captureException,
  captureMessage,
  trackErrors,
  withTransaction,
  createExpressApp,
};
