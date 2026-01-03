/**
 * Bugsink/Sentry SDK Integration Example for Java
 * ================================================
 *
 * This example demonstrates comprehensive error tracking integration
 * using the Sentry SDK with a self-hosted Bugsink server.
 *
 * Maven Dependencies:
 *     <dependency>
 *         <groupId>io.sentry</groupId>
 *         <artifactId>sentry</artifactId>
 *         <version>7.0.0</version>
 *     </dependency>
 *     <dependency>
 *         <groupId>io.sentry</groupId>
 *         <artifactId>sentry-spring-boot-starter-jakarta</artifactId>
 *         <version>7.0.0</version>
 *     </dependency>
 *
 * Gradle Dependencies:
 *     implementation 'io.sentry:sentry:7.0.0'
 *     implementation 'io.sentry:sentry-spring-boot-starter-jakarta:7.0.0'
 *
 * DSN Format:
 *     https://<project-key>@<your-bugsink-host>/<project-id>
 */

package com.example.sentry;

import io.sentry.*;
import io.sentry.protocol.User;
import io.sentry.protocol.SentryId;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.function.Supplier;

/**
 * Main Sentry integration service.
 * Provides comprehensive error tracking and performance monitoring.
 */
public class JavaExample {

    // =============================================================================
    // CONFIGURATION
    // =============================================================================

    private static final String SENTRY_DSN = System.getenv("SENTRY_DSN") != null
            ? System.getenv("SENTRY_DSN")
            : "https://your-project-key@errors.observability.app.bauer-group.com/1";

    private static final String ENVIRONMENT = System.getenv("ENVIRONMENT") != null
            ? System.getenv("ENVIRONMENT")
            : "development";

    private static final String RELEASE = System.getenv("APP_VERSION") != null
            ? System.getenv("APP_VERSION")
            : "1.0.0";

    // =============================================================================
    // SENTRY SERVICE
    // =============================================================================

    /**
     * Singleton service for Sentry operations.
     */
    public static class SentryService {
        private static SentryService instance;
        private boolean initialized = false;

        private SentryService() {}

        public static synchronized SentryService getInstance() {
            if (instance == null) {
                instance = new SentryService();
            }
            return instance;
        }

        /**
         * Initialize Sentry SDK.
         * Call this once at application startup.
         */
        public void init() {
            if (initialized) {
                System.out.println("Sentry already initialized");
                return;
            }

            Sentry.init(options -> {
                options.setDsn(SENTRY_DSN);
                options.setEnvironment(ENVIRONMENT);
                options.setRelease("my-app@" + RELEASE);

                // Performance Monitoring
                options.setTracesSampleRate(ENVIRONMENT.equals("production") ? 0.1 : 1.0);
                options.setProfilesSampleRate(0.1);

                // Error Sampling
                options.setSampleRate(1.0);

                // Data Handling
                options.setSendDefaultPii(false);
                options.setMaxBreadcrumbs(50);
                options.setAttachStacktrace(true);

                // Before Send Hook
                options.setBeforeSend((event, hint) -> beforeSendHandler(event, hint));

                // Before Breadcrumb Hook
                options.setBeforeBreadcrumb((breadcrumb, hint) -> beforeBreadcrumbHandler(breadcrumb, hint));

                // Debug mode
                options.setDebug(ENVIRONMENT.equals("development"));
            });

            // Set global tags
            Sentry.setTag("app.component", "backend");
            Sentry.setTag("app.runtime", "java");
            Sentry.setTag("app.version", System.getProperty("java.version"));

            initialized = true;
            System.out.println("Sentry initialized for environment: " + ENVIRONMENT);
        }

        /**
         * Process events before sending.
         */
        private static SentryEvent beforeSendHandler(SentryEvent event, Hint hint) {
            // Sanitize sensitive headers
            if (event.getRequest() != null && event.getRequest().getHeaders() != null) {
                Map<String, String> headers = new HashMap<>(event.getRequest().getHeaders());
                String[] sensitiveHeaders = {"Authorization", "Cookie", "X-API-Key"};
                for (String header : sensitiveHeaders) {
                    if (headers.containsKey(header)) {
                        headers.put(header, "[REDACTED]");
                    }
                }
                event.getRequest().setHeaders(headers);
            }

            // Filter specific exceptions
            Throwable throwable = hint.getAs(TypeCheckHint.SENTRY_TYPE_CHECK_HINT, Throwable.class);
            if (throwable != null && throwable.getClass().getSimpleName().equals("ExpectedBusinessException")) {
                return null; // Don't send this event
            }

            return event;
        }

        /**
         * Process breadcrumbs before adding.
         */
        private static Breadcrumb beforeBreadcrumbHandler(Breadcrumb breadcrumb, Hint hint) {
            // Filter health check requests
            if ("http".equals(breadcrumb.getCategory())) {
                Object url = breadcrumb.getData("url");
                if (url != null && url.toString().contains("/health")) {
                    return null;
                }
            }

            return breadcrumb;
        }

        /**
         * Set user context.
         */
        public void setUser(String userId, String email, String username, String ipAddress) {
            User user = new User();
            user.setId(userId);
            user.setEmail(email);
            user.setUsername(username);
            user.setIpAddress(ipAddress);
            Sentry.setUser(user);
        }

        /**
         * Set user with additional data.
         */
        public void setUser(String userId, String email, String username, String ipAddress,
                           Map<String, String> additionalData) {
            User user = new User();
            user.setId(userId);
            user.setEmail(email);
            user.setUsername(username);
            user.setIpAddress(ipAddress);
            if (additionalData != null) {
                user.setData(additionalData);
            }
            Sentry.setUser(user);
        }

        /**
         * Clear user context.
         */
        public void clearUser() {
            Sentry.setUser(null);
        }

        /**
         * Add a breadcrumb.
         */
        public void addBreadcrumb(String message, String category, SentryLevel level,
                                  Map<String, Object> data) {
            Breadcrumb breadcrumb = new Breadcrumb();
            breadcrumb.setMessage(message);
            breadcrumb.setCategory(category != null ? category : "custom");
            breadcrumb.setLevel(level != null ? level : SentryLevel.INFO);
            if (data != null) {
                data.forEach(breadcrumb::setData);
            }
            Sentry.addBreadcrumb(breadcrumb);
        }

        /**
         * Add a simple breadcrumb.
         */
        public void addBreadcrumb(String message, String category) {
            addBreadcrumb(message, category, SentryLevel.INFO, null);
        }

        /**
         * Set a tag.
         */
        public void setTag(String key, String value) {
            Sentry.setTag(key, value);
        }

        /**
         * Set extra context.
         */
        public void setExtra(String key, Object value) {
            Sentry.setExtra(key, value);
        }

        /**
         * Set custom context.
         */
        public void setContext(String name, Map<String, Object> context) {
            Sentry.setContext(name, context);
        }

        /**
         * Capture an exception.
         */
        public SentryId captureException(Throwable throwable) {
            return Sentry.captureException(throwable);
        }

        /**
         * Capture an exception with extra context.
         */
        public SentryId captureException(Throwable throwable, Map<String, Object> extraContext) {
            return Sentry.withScope(scope -> {
                if (extraContext != null) {
                    extraContext.forEach(scope::setExtra);
                }
                return Sentry.captureException(throwable);
            });
        }

        /**
         * Capture a message.
         */
        public SentryId captureMessage(String message, SentryLevel level) {
            return Sentry.captureMessage(message, level);
        }

        /**
         * Capture a message with extra context.
         */
        public SentryId captureMessage(String message, SentryLevel level,
                                       Map<String, Object> extraContext) {
            return Sentry.withScope(scope -> {
                if (extraContext != null) {
                    extraContext.forEach(scope::setExtra);
                }
                return Sentry.captureMessage(message, level);
            });
        }

        /**
         * Execute a callback within a transaction.
         */
        public <T> T withTransaction(String name, String operation, Supplier<T> callback) {
            ITransaction transaction = Sentry.startTransaction(name, operation);
            try {
                T result = callback.get();
                transaction.setStatus(SpanStatus.OK);
                return result;
            } catch (Exception e) {
                transaction.setStatus(SpanStatus.INTERNAL_ERROR);
                transaction.setThrowable(e);
                throw e;
            } finally {
                transaction.finish();
            }
        }

        /**
         * Execute a callback within a child span.
         */
        public <T> T withSpan(ITransaction transaction, String operation, String description,
                              Supplier<T> callback) {
            ISpan span = transaction.startChild(operation, description);
            try {
                T result = callback.get();
                span.setStatus(SpanStatus.OK);
                return result;
            } catch (Exception e) {
                span.setStatus(SpanStatus.INTERNAL_ERROR);
                span.setThrowable(e);
                throw e;
            } finally {
                span.finish();
            }
        }

        /**
         * Execute within a scope.
         */
        public <T> T withScope(java.util.function.Function<IScope, T> callback) {
            return Sentry.withScope(callback::apply);
        }

        /**
         * Flush pending events.
         */
        public void flush(long timeoutMillis) {
            Sentry.flush(timeoutMillis);
        }
    }

    // =============================================================================
    // EXAMPLE SERVICE
    // =============================================================================

    /**
     * Example service demonstrating Sentry integration patterns.
     */
    public static class ExampleService {
        private final SentryService sentry;

        public ExampleService() {
            this.sentry = SentryService.getInstance();
        }

        /**
         * Example method with error tracking.
         */
        public String fetchData(String id) {
            sentry.addBreadcrumb("Fetching data for " + id, "service");

            if ("error".equals(id)) {
                throw new RuntimeException("Failed to fetch data");
            }

            return "Data for " + id;
        }

        /**
         * Example method with transaction tracking.
         */
        public int processBatch(String[] items) {
            return sentry.withTransaction("process_batch", "task", () -> {
                int processed = 0;

                ITransaction transaction = Sentry.getSpan() != null
                        ? (ITransaction) Sentry.getSpan()
                        : null;

                for (String item : items) {
                    if (transaction != null) {
                        ISpan span = transaction.startChild("task.item", "process_" + item);
                        try {
                            Thread.sleep(50); // Simulate work
                            processed++;
                            span.setStatus(SpanStatus.OK);
                        } catch (InterruptedException e) {
                            span.setStatus(SpanStatus.INTERNAL_ERROR);
                            Thread.currentThread().interrupt();
                        } finally {
                            span.finish();
                        }
                    } else {
                        try {
                            Thread.sleep(50);
                            processed++;
                        } catch (InterruptedException e) {
                            Thread.currentThread().interrupt();
                        }
                    }
                }

                return processed;
            });
        }

        /**
         * Async operation example.
         */
        public CompletableFuture<String> asyncOperation(String input) {
            return CompletableFuture.supplyAsync(() -> {
                // Clone the hub for async context
                IHub hub = Sentry.getCurrentHub().clone();

                return hub.withScope(scope -> {
                    scope.setTag("async", "true");
                    scope.setExtra("input", input);

                    try {
                        Thread.sleep(100);
                        return "Processed: " + input;
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                        hub.captureException(e);
                        return "Error";
                    }
                });
            });
        }
    }

    // =============================================================================
    // SPRING BOOT CONFIGURATION EXAMPLE
    // =============================================================================

    /**
     * Spring Boot configuration example.
     *
     * Add to application.properties or application.yml:
     *
     * sentry.dsn=https://your-key@errors.observability.app.bauer-group.com/1
     * sentry.environment=production
     * sentry.release=my-app@1.0.0
     * sentry.traces-sample-rate=0.1
     * sentry.send-default-pii=false
     * sentry.max-breadcrumbs=50
     *
     * Or use programmatic configuration:
     */
    /*
    @Configuration
    public class SentryConfiguration {

        @Bean
        public SentryOptions.BeforeSendCallback beforeSendCallback() {
            return (event, hint) -> {
                // Custom filtering logic
                return event;
            };
        }

        @Bean
        public SentryOptions.BeforeBreadcrumbCallback beforeBreadcrumbCallback() {
            return (breadcrumb, hint) -> {
                // Custom breadcrumb filtering
                return breadcrumb;
            };
        }
    }

    @RestController
    @RequestMapping("/api")
    public class ApiController {

        @GetMapping("/users/{id}")
        public ResponseEntity<User> getUser(@PathVariable String id) {
            Sentry.addBreadcrumb("Fetching user " + id);

            // Your logic here

            return ResponseEntity.ok(user);
        }

        @ExceptionHandler(Exception.class)
        public ResponseEntity<ErrorResponse> handleException(Exception e) {
            SentryId eventId = Sentry.captureException(e);
            return ResponseEntity
                    .status(500)
                    .body(new ErrorResponse(e.getMessage(), eventId.toString()));
        }
    }
    */

    // =============================================================================
    // MAIN EXAMPLE
    // =============================================================================

    public static void main(String[] args) {
        System.out.println("=".repeat(60));
        System.out.println("Bugsink/Sentry Java SDK Integration Example");
        System.out.println("=".repeat(60));

        // Initialize Sentry
        SentryService sentry = SentryService.getInstance();
        sentry.init();

        // Set user context
        Map<String, String> userData = new HashMap<>();
        userData.put("subscriptionTier", "premium");
        sentry.setUser("user-123", "developer@example.com", "developer", "127.0.0.1", userData);

        // Add breadcrumbs
        sentry.addBreadcrumb("Application started", "app");
        sentry.addBreadcrumb("User authenticated", "auth");

        // Example 1: Capture handled exception
        System.out.println("\n1. Capturing handled exception...");
        try {
            int result = 10 / 0;
        } catch (ArithmeticException e) {
            Map<String, Object> context = new HashMap<>();
            context.put("operation", "division");
            context.put("numerator", 10);
            context.put("denominator", 0);

            SentryId eventId = sentry.captureException(e, context);
            System.out.println("   Exception captured: " + eventId);
        }

        // Example 2: Capture message
        System.out.println("\n2. Capturing info message...");
        Map<String, Object> messageContext = new HashMap<>();
        messageContext.put("stepsCompleted", 5);
        messageContext.put("timeTakenSeconds", 120);

        SentryId messageId = sentry.captureMessage(
                "User completed onboarding flow",
                SentryLevel.INFO,
                messageContext
        );
        System.out.println("   Message captured: " + messageId);

        // Example 3: Use example service
        System.out.println("\n3. Using example service...");
        ExampleService service = new ExampleService();
        try {
            String data = service.fetchData("123");
            System.out.println("   Data fetched: " + data);
        } catch (Exception e) {
            System.out.println("   Error handled");
        }

        // Example 4: Transaction with service
        System.out.println("\n4. Processing batch with transaction...");
        int processed = service.processBatch(new String[]{"a", "b", "c"});
        System.out.println("   Processed " + processed + " items");

        // Example 5: Scoped context
        System.out.println("\n5. Using scoped context...");
        sentry.withScope(scope -> {
            scope.setTag("feature", "new_checkout");
            scope.setExtra("cartItems", 3);
            scope.setExtra("totalAmount", 99.99);

            Sentry.captureMessage("Checkout initiated", SentryLevel.INFO);
            return null;
        });
        System.out.println("   Scoped message captured");

        // Example 6: Manual transaction with spans
        System.out.println("\n6. Creating transaction with spans...");
        ITransaction transaction = Sentry.startTransaction("order_processing", "task");
        try {
            ISpan fetchSpan = transaction.startChild("db.query", "Fetch order");
            Thread.sleep(50);
            fetchSpan.setStatus(SpanStatus.OK);
            fetchSpan.finish();

            ISpan paymentSpan = transaction.startChild("http.client", "Payment API");
            Thread.sleep(100);
            paymentSpan.setStatus(SpanStatus.OK);
            paymentSpan.finish();

            ISpan updateSpan = transaction.startChild("db.query", "Update order status");
            Thread.sleep(50);
            updateSpan.setStatus(SpanStatus.OK);
            updateSpan.finish();

            transaction.setStatus(SpanStatus.OK);
        } catch (InterruptedException e) {
            transaction.setStatus(SpanStatus.INTERNAL_ERROR);
            Thread.currentThread().interrupt();
        } finally {
            transaction.finish();
        }
        System.out.println("   Transaction with spans recorded");

        // Example 7: Async operation
        System.out.println("\n7. Async operation...");
        try {
            String asyncResult = service.asyncOperation("test-input").get();
            System.out.println("   Async result: " + asyncResult);
        } catch (Exception e) {
            System.out.println("   Async error: " + e.getMessage());
        }

        // Clean up
        sentry.clearUser();

        System.out.println("\n" + "=".repeat(60));
        System.out.println("All examples completed!");
        System.out.println("Check your Bugsink dashboard");
        System.out.println("=".repeat(60));

        // Flush events before exit
        sentry.flush(5000);
    }
}
