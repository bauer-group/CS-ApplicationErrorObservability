/**
 * Bugsink/Sentry SDK Integration Example for TypeScript
 * ======================================================
 *
 * This example demonstrates comprehensive error tracking integration
 * using the Sentry SDK with a self-hosted Bugsink server.
 *
 * Requirements:
 *     npm install @sentry/node @sentry/profiling-node express
 *     npm install -D typescript @types/node @types/express
 *
 * DSN Format:
 *     https://<project-key>@<your-bugsink-host>/<project-id>
 */

import * as Sentry from "@sentry/node";
import { nodeProfilingIntegration } from "@sentry/profiling-node";
import type { Event, EventHint, Breadcrumb, BreadcrumbHint } from "@sentry/types";
import * as os from "os";

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

interface UserContext {
  id: string;
  email?: string;
  username?: string;
  ipAddress?: string;
  [key: string]: unknown;
}

interface SentryConfig {
  dsn: string;
  environment: string;
  release: string;
  serverName: string;
  debug?: boolean;
}

type SeverityLevel = "debug" | "info" | "warning" | "error" | "fatal";

interface BreadcrumbOptions {
  message: string;
  category?: string;
  level?: SeverityLevel;
  data?: Record<string, unknown>;
}

interface TransactionOptions {
  name: string;
  op?: string;
  description?: string;
}

// =============================================================================
// CONFIGURATION
// =============================================================================

const SENTRY_DSN: string =
  process.env.SENTRY_DSN ||
  "https://your-project-key@errors.observability.app.bauer-group.com/1";

const ENVIRONMENT: string = process.env.NODE_ENV || "development";
const RELEASE: string = process.env.APP_VERSION || "1.0.0";
const SERVER_NAME: string = process.env.HOSTNAME || os.hostname();

// =============================================================================
// SENTRY SERVICE CLASS
// =============================================================================

/**
 * Singleton service for Sentry integration.
 * Provides type-safe methods for error tracking and monitoring.
 */
class SentryService {
  private static instance: SentryService;
  private initialized: boolean = false;

  private constructor() {}

  /**
   * Get the singleton instance.
   */
  static getInstance(): SentryService {
    if (!SentryService.instance) {
      SentryService.instance = new SentryService();
    }
    return SentryService.instance;
  }

  /**
   * Initialize Sentry with configuration.
   */
  init(config?: Partial<SentryConfig>): void {
    if (this.initialized) {
      console.warn("Sentry already initialized");
      return;
    }

    const finalConfig: SentryConfig = {
      dsn: config?.dsn || SENTRY_DSN,
      environment: config?.environment || ENVIRONMENT,
      release: config?.release || `my-app@${RELEASE}`,
      serverName: config?.serverName || SERVER_NAME,
      debug: config?.debug ?? ENVIRONMENT === "development",
    };

    Sentry.init({
      dsn: finalConfig.dsn,
      environment: finalConfig.environment,
      release: finalConfig.release,
      serverName: finalConfig.serverName,

      integrations: [nodeProfilingIntegration()],

      // Performance Monitoring
      tracesSampleRate: finalConfig.environment === "production" ? 0.1 : 1.0,
      profilesSampleRate: 0.1,

      // Error Sampling
      sampleRate: 1.0,

      // Data Handling
      sendDefaultPii: false,
      maxBreadcrumbs: 50,
      attachStacktrace: true,

      // Hooks
      beforeSend: this.beforeSendHandler.bind(this),
      beforeBreadcrumb: this.beforeBreadcrumbHandler.bind(this),

      debug: finalConfig.debug,
    });

    // Set global tags
    Sentry.setTag("app.component", "backend");
    Sentry.setTag("app.runtime", "nodejs");
    Sentry.setTag("app.language", "typescript");

    this.initialized = true;
    console.log(`Sentry initialized for environment: ${finalConfig.environment}`);
  }

  /**
   * Process events before sending.
   */
  private beforeSendHandler(event: Event, hint: EventHint): Event | null {
    // Sanitize sensitive headers
    if (event.request?.headers) {
      const sensitiveHeaders = ["authorization", "cookie", "x-api-key"];
      sensitiveHeaders.forEach((header) => {
        if (event.request!.headers![header]) {
          event.request!.headers![header] = "[REDACTED]";
        }
      });
    }

    // Filter specific exceptions
    const exception = hint.originalException as Error | undefined;
    if (exception?.name === "ExpectedBusinessError") {
      return null;
    }

    return event;
  }

  /**
   * Process breadcrumbs before adding.
   */
  private beforeBreadcrumbHandler(
    breadcrumb: Breadcrumb,
    hint?: BreadcrumbHint
  ): Breadcrumb | null {
    // Filter health check requests
    if (
      breadcrumb.category === "http" &&
      breadcrumb.data?.url?.toString().includes("/health")
    ) {
      return null;
    }

    return breadcrumb;
  }

  /**
   * Set user context.
   */
  setUser(user: UserContext | null): void {
    if (user) {
      Sentry.setUser({
        id: user.id,
        email: user.email,
        username: user.username,
        ip_address: user.ipAddress,
      });
    } else {
      Sentry.setUser(null);
    }
  }

  /**
   * Add a breadcrumb.
   */
  addBreadcrumb(options: BreadcrumbOptions): void {
    Sentry.addBreadcrumb({
      message: options.message,
      category: options.category || "custom",
      level: options.level || "info",
      data: options.data,
      timestamp: Date.now() / 1000,
    });
  }

  /**
   * Set custom context.
   */
  setContext(name: string, context: Record<string, unknown>): void {
    Sentry.setContext(name, context);
  }

  /**
   * Set a tag.
   */
  setTag(key: string, value: string): void {
    Sentry.setTag(key, value);
  }

  /**
   * Capture an exception.
   */
  captureException(
    error: Error,
    context?: Record<string, unknown>
  ): string | undefined {
    return Sentry.withScope((scope) => {
      if (context) {
        Object.entries(context).forEach(([key, value]) => {
          scope.setExtra(key, value);
        });
      }
      return Sentry.captureException(error);
    });
  }

  /**
   * Capture a message.
   */
  captureMessage(
    message: string,
    level: SeverityLevel = "info",
    context?: Record<string, unknown>
  ): string | undefined {
    return Sentry.withScope((scope) => {
      if (context) {
        Object.entries(context).forEach(([key, value]) => {
          scope.setExtra(key, value);
        });
      }
      return Sentry.captureMessage(message, level);
    });
  }

  /**
   * Start a transaction/span.
   */
  async startSpan<T>(
    options: TransactionOptions,
    callback: () => Promise<T> | T
  ): Promise<T> {
    return Sentry.startSpan(
      {
        name: options.name,
        op: options.op || "function",
      },
      async () => callback()
    );
  }

  /**
   * Execute callback within a scope.
   */
  withScope<T>(callback: (scope: Sentry.Scope) => T): T {
    return Sentry.withScope(callback);
  }

  /**
   * Flush pending events.
   */
  async flush(timeout: number = 5000): Promise<boolean> {
    return Sentry.flush(timeout);
  }
}

// =============================================================================
// DECORATORS
// =============================================================================

/**
 * Method decorator for automatic error tracking.
 *
 * @example
 * class UserService {
 *   @TrackErrors("fetch_user")
 *   async getUser(id: string): Promise<User> {
 *     // ...
 *   }
 * }
 */
function TrackErrors(operationName: string) {
  return function (
    target: unknown,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: unknown[]) {
      const sentry = SentryService.getInstance();

      return Sentry.withScope(async (scope) => {
        scope.setTag("operation", operationName);
        scope.setExtra("method", propertyKey);

        sentry.addBreadcrumb({
          message: `Executing ${operationName}`,
          category: "function",
          level: "info",
        });

        try {
          return await originalMethod.apply(this, args);
        } catch (error) {
          scope.setExtra("error_type", (error as Error).name);
          throw error;
        }
      });
    };

    return descriptor;
  };
}

/**
 * Method decorator for performance transaction tracking.
 *
 * @example
 * class OrderService {
 *   @Transaction("process_order", "task")
 *   async processOrder(orderId: string): Promise<void> {
 *     // ...
 *   }
 * }
 */
function Transaction(name: string, op: string = "function") {
  return function (
    target: unknown,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: unknown[]) {
      return Sentry.startSpan(
        {
          name,
          op,
        },
        async (span) => {
          try {
            const result = await originalMethod.apply(this, args);
            span.setStatus({ code: 1 }); // OK
            return result;
          } catch (error) {
            span.setStatus({ code: 2, message: (error as Error).message });
            throw error;
          }
        }
      );
    };

    return descriptor;
  };
}

// =============================================================================
// EXPRESS INTEGRATION
// =============================================================================

/**
 * Create an Express app with Sentry integration (if Express is available).
 */
async function createExpressApp(): Promise<unknown | null> {
  try {
    const express = await import("express");
    const app = express.default();

    // Sentry handlers
    app.use(Sentry.Handlers.requestHandler());
    app.use(Sentry.Handlers.tracingHandler());

    app.use(express.json());

    // Routes
    app.get("/", (req: express.Request, res: express.Response) => {
      const sentry = SentryService.getInstance();
      sentry.addBreadcrumb({ message: "Homepage visited", category: "navigation" });
      res.json({ status: "ok" });
    });

    app.get("/api/error", () => {
      throw new Error("Test error");
    });

    // Error handler
    app.use(Sentry.Handlers.errorHandler());

    app.use(
      (
        err: Error,
        req: express.Request,
        res: express.Response,
        next: express.NextFunction
      ) => {
        res.status(500).json({ error: err.message });
      }
    );

    return app;
  } catch {
    console.log("Express not available");
    return null;
  }
}

// =============================================================================
// EXAMPLE SERVICE CLASS
// =============================================================================

class ExampleService {
  private sentry: SentryService;

  constructor() {
    this.sentry = SentryService.getInstance();
  }

  @TrackErrors("fetch_data")
  async fetchData(id: string): Promise<{ id: string; data: string }> {
    this.sentry.addBreadcrumb({
      message: `Fetching data for ${id}`,
      category: "service",
      data: { id },
    });

    if (id === "error") {
      throw new Error("Failed to fetch data");
    }

    return { id, data: "Sample data" };
  }

  @Transaction("process_batch", "task")
  async processBatch(items: string[]): Promise<number> {
    let processed = 0;

    for (const item of items) {
      await Sentry.startSpan(
        { name: `process_item_${item}`, op: "task.item" },
        async () => {
          await this.sleep(50);
          processed++;
        }
      );
    }

    return processed;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

// =============================================================================
// MAIN EXAMPLE
// =============================================================================

async function main(): Promise<void> {
  console.log("=".repeat(60));
  console.log("Bugsink/Sentry TypeScript SDK Integration Example");
  console.log("=".repeat(60));

  // Get Sentry instance and initialize
  const sentry = SentryService.getInstance();
  sentry.init();

  // Set user context
  sentry.setUser({
    id: "user-123",
    email: "developer@example.com",
    username: "developer",
  });

  // Add breadcrumbs
  sentry.addBreadcrumb({ message: "Application started", category: "app" });
  sentry.addBreadcrumb({ message: "User authenticated", category: "auth" });

  // Example 1: Capture handled exception
  console.log("\n1. Capturing handled exception...");
  try {
    throw new Error("Test error");
  } catch (error) {
    const eventId = sentry.captureException(error as Error, {
      operation: "test",
    });
    console.log(`   Exception captured: ${eventId}`);
  }

  // Example 2: Capture message
  console.log("\n2. Capturing info message...");
  const messageId = sentry.captureMessage(
    "User completed action",
    "info",
    { action: "test" }
  );
  console.log(`   Message captured: ${messageId}`);

  // Example 3: Use decorated service
  console.log("\n3. Using decorated service methods...");
  const service = new ExampleService();

  try {
    const data = await service.fetchData("123");
    console.log(`   Data fetched: ${JSON.stringify(data)}`);
  } catch (error) {
    console.log("   Error handled");
  }

  // Example 4: Transaction with decorated method
  console.log("\n4. Processing batch with transaction...");
  const processed = await service.processBatch(["a", "b", "c"]);
  console.log(`   Processed ${processed} items`);

  // Example 5: Manual span
  console.log("\n5. Creating manual span...");
  await sentry.startSpan({ name: "manual_operation", op: "custom" }, async () => {
    await new Promise((r) => setTimeout(r, 100));
  });
  console.log("   Span completed");

  // Clean up
  sentry.setUser(null);

  console.log("\n" + "=".repeat(60));
  console.log("All examples completed!");
  console.log("=".repeat(60));

  await sentry.flush();
}

// Export for use as module
export {
  SentryService,
  TrackErrors,
  Transaction,
  createExpressApp,
  UserContext,
  SeverityLevel,
  BreadcrumbOptions,
  TransactionOptions,
};

// Run if executed directly
main().catch(console.error);
