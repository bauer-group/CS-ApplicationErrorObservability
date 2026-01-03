/**
 * Bugsink/Sentry SDK Integration Example for C/C++
 * =================================================
 *
 * This example demonstrates comprehensive error tracking integration
 * using the Sentry Native SDK with a self-hosted Bugsink server.
 *
 * Requirements:
 *     - sentry-native SDK: https://github.com/getsentry/sentry-native
 *     - CMake 3.14+
 *
 * Build with CMake:
 *     cmake -B build
 *     cmake --build build
 *
 * Or compile directly (adjust paths):
 *     g++ -std=c++17 -I/path/to/sentry/include -L/path/to/sentry/lib \
 *         -o example cpp_example.cpp -lsentry
 *
 * DSN Format:
 *     https://<project-key>@<your-bugsink-host>/<project-id>
 *
 * CMakeLists.txt example:
 *
 *     cmake_minimum_required(VERSION 3.14)
 *     project(sentry_example)
 *
 *     set(CMAKE_CXX_STANDARD 17)
 *
 *     include(FetchContent)
 *     FetchContent_Declare(
 *         sentry
 *         GIT_REPOSITORY https://github.com/getsentry/sentry-native.git
 *         GIT_TAG 0.7.0
 *     )
 *     FetchContent_MakeAvailable(sentry)
 *
 *     add_executable(example cpp_example.cpp)
 *     target_link_libraries(example PRIVATE sentry)
 */

#include <sentry.h>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <chrono>
#include <thread>
#include <memory>
#include <functional>

// =============================================================================
// CONFIGURATION
// =============================================================================

namespace Config {
    inline std::string getDsn() {
        const char* dsn = std::getenv("SENTRY_DSN");
        return dsn ? dsn : "https://your-project-key@errors.observability.app.bauer-group.com/1";
    }

    inline std::string getEnvironment() {
        const char* env = std::getenv("ENVIRONMENT");
        return env ? env : "development";
    }

    inline std::string getRelease() {
        const char* release = std::getenv("APP_VERSION");
        return release ? release : "1.0.0";
    }

    inline bool isProduction() {
        return getEnvironment() == "production";
    }
}

// =============================================================================
// SENTRY SERVICE CLASS
// =============================================================================

/**
 * RAII wrapper for Sentry SDK.
 * Provides comprehensive error tracking and crash reporting.
 */
class SentryService {
public:
    /**
     * Initialize Sentry SDK.
     * @param database_path Path for crash database storage
     */
    explicit SentryService(const std::string& database_path = ".sentry-native") {
        sentry_options_t* options = sentry_options_new();

        // Basic configuration
        sentry_options_set_dsn(options, Config::getDsn().c_str());
        sentry_options_set_environment(options, Config::getEnvironment().c_str());
        sentry_options_set_release(options, ("my-app@" + Config::getRelease()).c_str());

        // Database path for crash reports
        sentry_options_set_database_path(options, database_path.c_str());

        // Debug mode
        sentry_options_set_debug(options, Config::isProduction() ? 0 : 1);

        // Sample rate (1.0 = 100%)
        sentry_options_set_sample_rate(options, 1.0);

        // Max breadcrumbs
        sentry_options_set_max_breadcrumbs(options, 50);

        // Set before_send callback
        sentry_options_set_before_send(options, beforeSendCallback, nullptr);

        // Initialize
        int result = sentry_init(options);
        if (result != 0) {
            std::cerr << "Failed to initialize Sentry" << std::endl;
            m_initialized = false;
        } else {
            m_initialized = true;
            std::cout << "Sentry initialized for environment: " << Config::getEnvironment() << std::endl;
        }

        // Set global tags
        setTag("app.component", "backend");
        setTag("app.runtime", "cpp");

#ifdef __cplusplus
        setTag("app.cpp_standard", std::to_string(__cplusplus));
#endif
    }

    /**
     * Destructor - closes Sentry and flushes events.
     */
    ~SentryService() {
        if (m_initialized) {
            // Flush with 5 second timeout
            sentry_flush(5000);
            sentry_close();
        }
    }

    // Prevent copying
    SentryService(const SentryService&) = delete;
    SentryService& operator=(const SentryService&) = delete;

    /**
     * Check if Sentry is initialized.
     */
    bool isInitialized() const { return m_initialized; }

    /**
     * Set user context.
     */
    void setUser(const std::string& id,
                 const std::string& email = "",
                 const std::string& username = "",
                 const std::string& ipAddress = "") {
        sentry_value_t user = sentry_value_new_object();

        sentry_value_set_by_key(user, "id", sentry_value_new_string(id.c_str()));

        if (!email.empty()) {
            sentry_value_set_by_key(user, "email", sentry_value_new_string(email.c_str()));
        }
        if (!username.empty()) {
            sentry_value_set_by_key(user, "username", sentry_value_new_string(username.c_str()));
        }
        if (!ipAddress.empty()) {
            sentry_value_set_by_key(user, "ip_address", sentry_value_new_string(ipAddress.c_str()));
        }

        sentry_set_user(user);
    }

    /**
     * Set user with additional data.
     */
    void setUserWithData(const std::string& id,
                         const std::string& email,
                         const std::string& username,
                         const std::string& ipAddress,
                         sentry_value_t extra) {
        sentry_value_t user = sentry_value_new_object();

        sentry_value_set_by_key(user, "id", sentry_value_new_string(id.c_str()));
        sentry_value_set_by_key(user, "email", sentry_value_new_string(email.c_str()));
        sentry_value_set_by_key(user, "username", sentry_value_new_string(username.c_str()));
        sentry_value_set_by_key(user, "ip_address", sentry_value_new_string(ipAddress.c_str()));
        sentry_value_set_by_key(user, "data", extra);

        sentry_set_user(user);
    }

    /**
     * Clear user context.
     */
    void clearUser() {
        sentry_remove_user();
    }

    /**
     * Add a breadcrumb.
     */
    void addBreadcrumb(const std::string& message,
                       const std::string& category = "custom",
                       const std::string& level = "info",
                       sentry_value_t data = sentry_value_new_null()) {
        sentry_value_t breadcrumb = sentry_value_new_breadcrumb(nullptr, message.c_str());
        sentry_value_set_by_key(breadcrumb, "category", sentry_value_new_string(category.c_str()));
        sentry_value_set_by_key(breadcrumb, "level", sentry_value_new_string(level.c_str()));

        if (!sentry_value_is_null(data)) {
            sentry_value_set_by_key(breadcrumb, "data", data);
        }

        sentry_add_breadcrumb(breadcrumb);
    }

    /**
     * Set a tag.
     */
    void setTag(const std::string& key, const std::string& value) {
        sentry_set_tag(key.c_str(), value.c_str());
    }

    /**
     * Remove a tag.
     */
    void removeTag(const std::string& key) {
        sentry_remove_tag(key.c_str());
    }

    /**
     * Set extra context.
     */
    void setExtra(const std::string& key, sentry_value_t value) {
        sentry_set_extra(key.c_str(), value);
    }

    /**
     * Set extra context (string value).
     */
    void setExtra(const std::string& key, const std::string& value) {
        sentry_set_extra(key.c_str(), sentry_value_new_string(value.c_str()));
    }

    /**
     * Set extra context (int value).
     */
    void setExtra(const std::string& key, int value) {
        sentry_set_extra(key.c_str(), sentry_value_new_int32(value));
    }

    /**
     * Set extra context (double value).
     */
    void setExtra(const std::string& key, double value) {
        sentry_set_extra(key.c_str(), sentry_value_new_double(value));
    }

    /**
     * Remove extra context.
     */
    void removeExtra(const std::string& key) {
        sentry_remove_extra(key.c_str());
    }

    /**
     * Set custom context.
     */
    void setContext(const std::string& name, sentry_value_t context) {
        sentry_set_context(name.c_str(), context);
    }

    /**
     * Capture an exception/error message.
     * Returns the event UUID.
     */
    sentry_uuid_t captureMessage(const std::string& message,
                                  sentry_level_t level = SENTRY_LEVEL_ERROR) {
        sentry_value_t event = sentry_value_new_message_event(level, nullptr, message.c_str());
        return sentry_capture_event(event);
    }

    /**
     * Capture an exception with context.
     */
    sentry_uuid_t captureException(const std::string& type,
                                   const std::string& message,
                                   sentry_value_t extra = sentry_value_new_null()) {
        sentry_value_t event = sentry_value_new_event();

        // Create exception
        sentry_value_t exception = sentry_value_new_exception(type.c_str(), message.c_str());
        sentry_event_add_exception(event, exception);

        // Add extra context
        if (!sentry_value_is_null(extra)) {
            sentry_value_t contexts = sentry_value_new_object();
            sentry_value_set_by_key(contexts, "extra", extra);
            sentry_value_set_by_key(event, "contexts", contexts);
        }

        return sentry_capture_event(event);
    }

    /**
     * Start a transaction for performance monitoring.
     * Note: sentry-native has limited transaction support.
     */
    void startTransaction(const std::string& name, const std::string& operation) {
        // Create transaction context
        sentry_transaction_context_t* tx_ctx =
            sentry_transaction_context_new(name.c_str(), operation.c_str());

        // Start transaction
        m_currentTransaction = sentry_transaction_start(tx_ctx, sentry_value_new_null());
    }

    /**
     * Start a child span.
     */
    void startSpan(const std::string& operation, const std::string& description) {
        if (m_currentTransaction) {
            sentry_span_t* span = sentry_transaction_start_child(
                m_currentTransaction,
                operation.c_str(),
                description.c_str()
            );
            // Store span for later use if needed
            m_currentSpan = span;
        }
    }

    /**
     * Finish current span.
     */
    void finishSpan() {
        if (m_currentSpan) {
            sentry_span_finish(m_currentSpan);
            m_currentSpan = nullptr;
        }
    }

    /**
     * Finish current transaction.
     */
    void finishTransaction() {
        if (m_currentTransaction) {
            sentry_transaction_finish(m_currentTransaction);
            m_currentTransaction = nullptr;
        }
    }

    /**
     * Execute a function with automatic span tracking.
     */
    template<typename Func>
    auto withSpan(const std::string& operation,
                  const std::string& description,
                  Func&& func) -> decltype(func()) {
        startSpan(operation, description);
        try {
            auto result = func();
            finishSpan();
            return result;
        } catch (...) {
            finishSpan();
            throw;
        }
    }

    /**
     * Flush pending events.
     */
    bool flush(uint64_t timeoutMs = 5000) {
        return sentry_flush(timeoutMs) == 0;
    }

private:
    bool m_initialized = false;
    sentry_transaction_t* m_currentTransaction = nullptr;
    sentry_span_t* m_currentSpan = nullptr;

    /**
     * Before send callback for filtering/modifying events.
     */
    static sentry_value_t beforeSendCallback(sentry_value_t event,
                                              void* hint,
                                              void* closure) {
        // Get exception type if present
        sentry_value_t exception = sentry_value_get_by_key(event, "exception");
        if (!sentry_value_is_null(exception)) {
            sentry_value_t values = sentry_value_get_by_key(exception, "values");
            if (!sentry_value_is_null(values)) {
                size_t len = sentry_value_get_length(values);
                for (size_t i = 0; i < len; i++) {
                    sentry_value_t exc = sentry_value_get_by_index(values, i);
                    sentry_value_t type = sentry_value_get_by_key(exc, "type");
                    const char* type_str = sentry_value_as_string(type);

                    // Filter expected business exceptions
                    if (type_str && strcmp(type_str, "ExpectedBusinessException") == 0) {
                        sentry_value_decref(event);
                        return sentry_value_new_null();
                    }
                }
            }
        }

        // Sanitize sensitive headers
        sentry_value_t request = sentry_value_get_by_key(event, "request");
        if (!sentry_value_is_null(request)) {
            sentry_value_t headers = sentry_value_get_by_key(request, "headers");
            if (!sentry_value_is_null(headers)) {
                const char* sensitive[] = {"Authorization", "Cookie", "X-API-Key"};
                for (const char* header : sensitive) {
                    sentry_value_t val = sentry_value_get_by_key(headers, header);
                    if (!sentry_value_is_null(val)) {
                        sentry_value_set_by_key(headers, header,
                            sentry_value_new_string("[REDACTED]"));
                    }
                }
            }
        }

        return event;
    }
};

// =============================================================================
// EXAMPLE SERVICE
// =============================================================================

/**
 * Example service demonstrating Sentry integration patterns.
 */
class ExampleService {
public:
    explicit ExampleService(SentryService& sentry) : m_sentry(sentry) {}

    /**
     * Example method with error tracking.
     */
    std::string fetchData(const std::string& id) {
        sentry_value_t data = sentry_value_new_object();
        sentry_value_set_by_key(data, "id", sentry_value_new_string(id.c_str()));

        m_sentry.addBreadcrumb(
            "Fetching data for " + id,
            "service",
            "info",
            data
        );

        if (id == "error") {
            throw std::runtime_error("Failed to fetch data");
        }

        return "Data for " + id;
    }

    /**
     * Example method with transaction tracking.
     */
    int processBatch(const std::vector<std::string>& items) {
        m_sentry.startTransaction("process_batch", "task");

        int processed = 0;

        for (const auto& item : items) {
            m_sentry.startSpan("task.item", "process_" + item);

            // Simulate work
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
            processed++;

            m_sentry.finishSpan();
        }

        m_sentry.finishTransaction();

        return processed;
    }

private:
    SentryService& m_sentry;
};

// =============================================================================
// C API WRAPPER (for pure C usage)
// =============================================================================

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Initialize Sentry (C API wrapper).
 */
int sentry_service_init(const char* dsn, const char* environment, const char* release) {
    sentry_options_t* options = sentry_options_new();

    sentry_options_set_dsn(options, dsn);
    sentry_options_set_environment(options, environment);
    sentry_options_set_release(options, release);
    sentry_options_set_database_path(options, ".sentry-native");

    return sentry_init(options);
}

/**
 * Set user context (C API).
 */
void sentry_service_set_user(const char* id, const char* email, const char* username) {
    sentry_value_t user = sentry_value_new_object();
    sentry_value_set_by_key(user, "id", sentry_value_new_string(id));
    if (email) {
        sentry_value_set_by_key(user, "email", sentry_value_new_string(email));
    }
    if (username) {
        sentry_value_set_by_key(user, "username", sentry_value_new_string(username));
    }
    sentry_set_user(user);
}

/**
 * Add breadcrumb (C API).
 */
void sentry_service_add_breadcrumb(const char* message, const char* category) {
    sentry_value_t breadcrumb = sentry_value_new_breadcrumb(NULL, message);
    sentry_value_set_by_key(breadcrumb, "category", sentry_value_new_string(category));
    sentry_add_breadcrumb(breadcrumb);
}

/**
 * Capture message (C API).
 */
void sentry_service_capture_message(const char* message, int level) {
    sentry_value_t event = sentry_value_new_message_event(
        static_cast<sentry_level_t>(level),
        NULL,
        message
    );
    sentry_capture_event(event);
}

/**
 * Close Sentry (C API).
 */
void sentry_service_close(void) {
    sentry_flush(5000);
    sentry_close();
}

#ifdef __cplusplus
}
#endif

// =============================================================================
// MAIN EXAMPLE
// =============================================================================

int main() {
    std::cout << std::string(60, '=') << std::endl;
    std::cout << "Bugsink/Sentry C++ SDK Integration Example" << std::endl;
    std::cout << std::string(60, '=') << std::endl;

    // Initialize Sentry service
    SentryService sentry(".sentry-native");

    if (!sentry.isInitialized()) {
        std::cerr << "Failed to initialize Sentry" << std::endl;
        return 1;
    }

    // Set user context
    sentry_value_t userData = sentry_value_new_object();
    sentry_value_set_by_key(userData, "subscription_tier",
        sentry_value_new_string("premium"));

    sentry.setUserWithData(
        "user-123",
        "developer@example.com",
        "developer",
        "127.0.0.1",
        userData
    );

    // Add breadcrumbs
    sentry.addBreadcrumb("Application started", "app", "info");
    sentry.addBreadcrumb("User authenticated", "auth", "info");

    // Example 1: Capture handled exception
    std::cout << "\n1. Capturing handled exception..." << std::endl;
    try {
        throw std::runtime_error("Division by zero");
    } catch (const std::exception& e) {
        sentry_value_t extra = sentry_value_new_object();
        sentry_value_set_by_key(extra, "operation", sentry_value_new_string("division"));
        sentry_value_set_by_key(extra, "numerator", sentry_value_new_int32(10));
        sentry_value_set_by_key(extra, "denominator", sentry_value_new_int32(0));

        sentry_uuid_t eventId = sentry.captureException("RuntimeError", e.what(), extra);
        char uuid_str[37];
        sentry_uuid_as_string(&eventId, uuid_str);
        std::cout << "   Exception captured: " << uuid_str << std::endl;
    }

    // Example 2: Capture message
    std::cout << "\n2. Capturing info message..." << std::endl;
    sentry.setExtra("steps_completed", 5);
    sentry.setExtra("time_taken_seconds", 120);
    sentry_uuid_t msgId = sentry.captureMessage("User completed onboarding flow", SENTRY_LEVEL_INFO);
    char msg_uuid_str[37];
    sentry_uuid_as_string(&msgId, msg_uuid_str);
    std::cout << "   Message captured: " << msg_uuid_str << std::endl;

    // Example 3: Use example service
    std::cout << "\n3. Using example service..." << std::endl;
    ExampleService service(sentry);
    try {
        std::string data = service.fetchData("123");
        std::cout << "   Data fetched: " << data << std::endl;
    } catch (const std::exception& e) {
        std::cout << "   Error handled" << std::endl;
    }

    // Example 4: Transaction with service
    std::cout << "\n4. Processing batch with transaction..." << std::endl;
    std::vector<std::string> items = {"a", "b", "c"};
    int processed = service.processBatch(items);
    std::cout << "   Processed " << processed << " items" << std::endl;

    // Example 5: Scoped context with tags
    std::cout << "\n5. Using scoped context..." << std::endl;
    sentry.setTag("feature", "new_checkout");
    sentry.setExtra("cart_items", 3);
    sentry.setExtra("total_amount", 99.99);
    sentry.captureMessage("Checkout initiated", SENTRY_LEVEL_INFO);
    sentry.removeTag("feature");
    std::cout << "   Scoped message captured" << std::endl;

    // Example 6: Manual transaction with spans
    std::cout << "\n6. Creating transaction with spans..." << std::endl;
    sentry.startTransaction("order_processing", "task");

    sentry.startSpan("db.query", "Fetch order");
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    sentry.finishSpan();

    sentry.startSpan("http.client", "Payment API");
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    sentry.finishSpan();

    sentry.startSpan("db.query", "Update order status");
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    sentry.finishSpan();

    sentry.finishTransaction();
    std::cout << "   Transaction with spans recorded" << std::endl;

    // Clean up
    sentry.clearUser();

    std::cout << "\n" << std::string(60, '=') << std::endl;
    std::cout << "All examples completed!" << std::endl;
    std::cout << "Check your Bugsink dashboard" << std::endl;
    std::cout << std::string(60, '=') << std::endl;

    // Sentry is automatically flushed and closed in destructor
    return 0;
}
