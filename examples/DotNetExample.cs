/**
 * Bugsink/Sentry SDK Integration Example for C# / .NET
 * =====================================================
 *
 * This example demonstrates comprehensive error tracking integration
 * using the Sentry SDK with a self-hosted Bugsink server.
 *
 * NuGet Packages:
 *     dotnet add package Sentry
 *     dotnet add package Sentry.AspNetCore
 *     dotnet add package Sentry.Extensions.Logging
 *
 * DSN Format:
 *     https://<project-key>@<your-bugsink-host>/<project-id>
 */

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Sentry;
using Sentry.Protocol;

namespace BugsinkExample
{
    // =============================================================================
    // CONFIGURATION
    // =============================================================================

    public static class SentryConfig
    {
        public static string Dsn =>
            Environment.GetEnvironmentVariable("SENTRY_DSN")
            ?? "https://your-project-key@errors.observability.app.bauer-group.com/1";

        public static string Environment =>
            Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT")
            ?? Environment.GetEnvironmentVariable("DOTNET_ENVIRONMENT")
            ?? "development";

        public static string Release =>
            Environment.GetEnvironmentVariable("APP_VERSION") ?? "1.0.0";
    }

    // =============================================================================
    // SENTRY SERVICE
    // =============================================================================

    /// <summary>
    /// Singleton service for Sentry operations.
    /// Provides comprehensive error tracking and performance monitoring.
    /// </summary>
    public sealed class SentryService : IDisposable
    {
        private static readonly Lazy<SentryService> _instance =
            new Lazy<SentryService>(() => new SentryService());

        private IDisposable? _sentryDisposable;
        private bool _initialized = false;

        private SentryService() { }

        public static SentryService Instance => _instance.Value;

        /// <summary>
        /// Initialize Sentry SDK.
        /// Call this once at application startup.
        /// </summary>
        public void Init()
        {
            if (_initialized)
            {
                Console.WriteLine("Sentry already initialized");
                return;
            }

            _sentryDisposable = SentrySdk.Init(options =>
            {
                options.Dsn = SentryConfig.Dsn;
                options.Environment = SentryConfig.Environment;
                options.Release = $"my-app@{SentryConfig.Release}";

                // Performance Monitoring
                options.TracesSampleRate = SentryConfig.Environment == "production" ? 0.1 : 1.0;
                options.ProfilesSampleRate = 0.1;

                // Error Sampling
                options.SampleRate = 1.0f;

                // Data Handling
                options.SendDefaultPii = false;
                options.MaxBreadcrumbs = 50;
                options.AttachStacktrace = true;

                // Before Send Hook
                options.SetBeforeSend(BeforeSendHandler);

                // Before Breadcrumb Hook
                options.SetBeforeBreadcrumb(BeforeBreadcrumbHandler);

                // Debug mode
                options.Debug = SentryConfig.Environment == "development";
            });

            // Set global tags
            SentrySdk.ConfigureScope(scope =>
            {
                scope.SetTag("app.component", "backend");
                scope.SetTag("app.runtime", "dotnet");
                scope.SetTag("app.version", System.Runtime.InteropServices.RuntimeInformation.FrameworkDescription);
            });

            _initialized = true;
            Console.WriteLine($"Sentry initialized for environment: {SentryConfig.Environment}");
        }

        /// <summary>
        /// Process events before sending.
        /// </summary>
        private static SentryEvent? BeforeSendHandler(SentryEvent sentryEvent, Hint hint)
        {
            // Sanitize sensitive headers
            if (sentryEvent.Request?.Headers != null)
            {
                var sensitiveHeaders = new[] { "Authorization", "Cookie", "X-API-Key" };
                foreach (var header in sensitiveHeaders)
                {
                    if (sentryEvent.Request.Headers.ContainsKey(header))
                    {
                        sentryEvent.Request.Headers[header] = "[REDACTED]";
                    }
                }
            }

            // Filter specific exceptions
            if (hint.Exception is ExpectedBusinessException)
            {
                return null; // Don't send this event
            }

            return sentryEvent;
        }

        /// <summary>
        /// Process breadcrumbs before adding.
        /// </summary>
        private static Breadcrumb? BeforeBreadcrumbHandler(Breadcrumb breadcrumb, Hint hint)
        {
            // Filter health check requests
            if (breadcrumb.Category == "http" &&
                breadcrumb.Data?.TryGetValue("url", out var url) == true &&
                url?.ToString()?.Contains("/health") == true)
            {
                return null;
            }

            return breadcrumb;
        }

        /// <summary>
        /// Set user context.
        /// </summary>
        public void SetUser(string userId, string? email = null, string? username = null,
                           string? ipAddress = null, Dictionary<string, string>? additionalData = null)
        {
            SentrySdk.ConfigureScope(scope =>
            {
                scope.User = new SentryUser
                {
                    Id = userId,
                    Email = email,
                    Username = username,
                    IpAddress = ipAddress,
                    Other = additionalData ?? new Dictionary<string, string>()
                };
            });
        }

        /// <summary>
        /// Clear user context.
        /// </summary>
        public void ClearUser()
        {
            SentrySdk.ConfigureScope(scope => scope.User = null);
        }

        /// <summary>
        /// Add a breadcrumb.
        /// </summary>
        public void AddBreadcrumb(string message, string? category = null,
                                  BreadcrumbLevel level = BreadcrumbLevel.Info,
                                  Dictionary<string, string>? data = null)
        {
            SentrySdk.AddBreadcrumb(
                message: message,
                category: category ?? "custom",
                level: level,
                data: data
            );
        }

        /// <summary>
        /// Set a tag.
        /// </summary>
        public void SetTag(string key, string value)
        {
            SentrySdk.ConfigureScope(scope => scope.SetTag(key, value));
        }

        /// <summary>
        /// Set extra context.
        /// </summary>
        public void SetExtra(string key, object value)
        {
            SentrySdk.ConfigureScope(scope => scope.SetExtra(key, value));
        }

        /// <summary>
        /// Set custom context.
        /// </summary>
        public void SetContext(string name, Dictionary<string, object> context)
        {
            SentrySdk.ConfigureScope(scope => scope.Contexts[name] = context);
        }

        /// <summary>
        /// Capture an exception.
        /// </summary>
        public SentryId CaptureException(Exception exception)
        {
            return SentrySdk.CaptureException(exception);
        }

        /// <summary>
        /// Capture an exception with extra context.
        /// </summary>
        public SentryId CaptureException(Exception exception, Dictionary<string, object>? extraContext)
        {
            SentrySdk.ConfigureScope(scope =>
            {
                if (extraContext != null)
                {
                    foreach (var kvp in extraContext)
                    {
                        scope.SetExtra(kvp.Key, kvp.Value);
                    }
                }
            });

            return SentrySdk.CaptureException(exception);
        }

        /// <summary>
        /// Capture a message.
        /// </summary>
        public SentryId CaptureMessage(string message, SentryLevel level = SentryLevel.Info)
        {
            return SentrySdk.CaptureMessage(message, level);
        }

        /// <summary>
        /// Capture a message with extra context.
        /// </summary>
        public SentryId CaptureMessage(string message, SentryLevel level,
                                       Dictionary<string, object>? extraContext)
        {
            SentrySdk.ConfigureScope(scope =>
            {
                if (extraContext != null)
                {
                    foreach (var kvp in extraContext)
                    {
                        scope.SetExtra(kvp.Key, kvp.Value);
                    }
                }
            });

            return SentrySdk.CaptureMessage(message, level);
        }

        /// <summary>
        /// Execute a callback within a transaction.
        /// </summary>
        public T WithTransaction<T>(string name, string operation, Func<ITransactionTracer, T> callback)
        {
            var transaction = SentrySdk.StartTransaction(name, operation);
            SentrySdk.ConfigureScope(scope => scope.Transaction = transaction);

            try
            {
                var result = callback(transaction);
                transaction.Status = SpanStatus.Ok;
                return result;
            }
            catch (Exception)
            {
                transaction.Status = SpanStatus.InternalError;
                throw;
            }
            finally
            {
                transaction.Finish();
            }
        }

        /// <summary>
        /// Execute an async callback within a transaction.
        /// </summary>
        public async Task<T> WithTransactionAsync<T>(string name, string operation,
                                                      Func<ITransactionTracer, Task<T>> callback)
        {
            var transaction = SentrySdk.StartTransaction(name, operation);
            SentrySdk.ConfigureScope(scope => scope.Transaction = transaction);

            try
            {
                var result = await callback(transaction);
                transaction.Status = SpanStatus.Ok;
                return result;
            }
            catch (Exception)
            {
                transaction.Status = SpanStatus.InternalError;
                throw;
            }
            finally
            {
                transaction.Finish();
            }
        }

        /// <summary>
        /// Flush pending events.
        /// </summary>
        public async Task FlushAsync(TimeSpan timeout)
        {
            await SentrySdk.FlushAsync(timeout);
        }

        public void Dispose()
        {
            _sentryDisposable?.Dispose();
        }
    }

    // =============================================================================
    // CUSTOM EXCEPTIONS
    // =============================================================================

    public class ExpectedBusinessException : Exception
    {
        public ExpectedBusinessException(string message) : base(message) { }
    }

    // =============================================================================
    // EXAMPLE SERVICE
    // =============================================================================

    /// <summary>
    /// Example service demonstrating Sentry integration patterns.
    /// </summary>
    public class ExampleService
    {
        private readonly SentryService _sentry;

        public ExampleService()
        {
            _sentry = SentryService.Instance;
        }

        /// <summary>
        /// Example method with error tracking.
        /// </summary>
        public string FetchData(string id)
        {
            _sentry.AddBreadcrumb($"Fetching data for {id}", "service",
                data: new Dictionary<string, string> { { "id", id } });

            if (id == "error")
            {
                throw new InvalidOperationException("Failed to fetch data");
            }

            return $"Data for {id}";
        }

        /// <summary>
        /// Example method with transaction tracking.
        /// </summary>
        public async Task<int> ProcessBatchAsync(string[] items)
        {
            return await _sentry.WithTransactionAsync("process_batch", "task", async transaction =>
            {
                int processed = 0;

                foreach (var item in items)
                {
                    var span = transaction.StartChild("task.item", $"process_{item}");
                    try
                    {
                        await Task.Delay(50); // Simulate work
                        processed++;
                        span.Status = SpanStatus.Ok;
                    }
                    catch (Exception)
                    {
                        span.Status = SpanStatus.InternalError;
                        throw;
                    }
                    finally
                    {
                        span.Finish();
                    }
                }

                return processed;
            });
        }
    }

    // =============================================================================
    // ASP.NET CORE CONFIGURATION EXAMPLE
    // =============================================================================

    /*
    // Program.cs for ASP.NET Core 6+

    using Sentry.AspNetCore;

    var builder = WebApplication.CreateBuilder(args);

    // Add Sentry
    builder.WebHost.UseSentry(options =>
    {
        options.Dsn = "https://your-key@errors.observability.app.bauer-group.com/1";
        options.Environment = builder.Environment.EnvironmentName;
        options.Release = "my-app@1.0.0";
        options.TracesSampleRate = builder.Environment.IsProduction() ? 0.1 : 1.0;
        options.SendDefaultPii = false;
        options.MaxBreadcrumbs = 50;

        // Performance monitoring for all requests
        options.EnableTracing = true;

        // Before send hook
        options.SetBeforeSend((sentryEvent, hint) =>
        {
            // Filter or modify events
            return sentryEvent;
        });
    });

    builder.Services.AddControllers();

    var app = builder.Build();

    // Sentry middleware should be early in the pipeline
    app.UseSentryTracing();

    app.UseRouting();
    app.MapControllers();

    app.Run();


    // Example Controller
    [ApiController]
    [Route("api/[controller]")]
    public class UsersController : ControllerBase
    {
        private readonly IHub _sentryHub;

        public UsersController(IHub sentryHub)
        {
            _sentryHub = sentryHub;
        }

        [HttpGet("{id}")]
        public ActionResult<User> GetUser(string id)
        {
            _sentryHub.AddBreadcrumb($"Fetching user {id}");

            // Set additional context
            _sentryHub.ConfigureScope(scope =>
            {
                scope.SetTag("endpoint", "get_user");
                scope.SetExtra("userId", id);
            });

            // Your logic here
            return Ok(new { Id = id, Name = "Test User" });
        }

        [HttpPost]
        public ActionResult<User> CreateUser([FromBody] CreateUserRequest request)
        {
            using var _ = _sentryHub.PushScope();

            _sentryHub.ConfigureScope(scope =>
            {
                scope.SetTag("operation", "create_user");
            });

            try
            {
                // Your logic here
                return Ok(new { Id = Guid.NewGuid().ToString(), Name = request.Name });
            }
            catch (Exception ex)
            {
                _sentryHub.CaptureException(ex);
                return StatusCode(500, new { Error = ex.Message });
            }
        }
    }

    // Error handling middleware
    public class SentryErrorHandlingMiddleware
    {
        private readonly RequestDelegate _next;
        private readonly IHub _hub;

        public SentryErrorHandlingMiddleware(RequestDelegate next, IHub hub)
        {
            _next = next;
            _hub = hub;
        }

        public async Task InvokeAsync(HttpContext context)
        {
            try
            {
                await _next(context);
            }
            catch (Exception ex)
            {
                _hub.ConfigureScope(scope =>
                {
                    scope.SetExtra("requestPath", context.Request.Path);
                    scope.SetExtra("requestMethod", context.Request.Method);
                });

                var eventId = _hub.CaptureException(ex);

                context.Response.StatusCode = 500;
                await context.Response.WriteAsJsonAsync(new
                {
                    Error = ex.Message,
                    EventId = eventId.ToString()
                });
            }
        }
    }
    */

    // =============================================================================
    // MAIN EXAMPLE
    // =============================================================================

    public class Program
    {
        public static async Task Main(string[] args)
        {
            Console.WriteLine(new string('=', 60));
            Console.WriteLine("Bugsink/Sentry C#/.NET SDK Integration Example");
            Console.WriteLine(new string('=', 60));

            // Initialize Sentry
            var sentry = SentryService.Instance;
            sentry.Init();

            // Set user context
            sentry.SetUser(
                userId: "user-123",
                email: "developer@example.com",
                username: "developer",
                additionalData: new Dictionary<string, string>
                {
                    { "subscriptionTier", "premium" }
                }
            );

            // Add breadcrumbs
            sentry.AddBreadcrumb("Application started", "app");
            sentry.AddBreadcrumb("User authenticated", "auth");

            // Example 1: Capture handled exception
            Console.WriteLine("\n1. Capturing handled exception...");
            try
            {
                var result = 10 / int.Parse("0");
            }
            catch (DivideByZeroException ex)
            {
                var eventId = sentry.CaptureException(ex, new Dictionary<string, object>
                {
                    { "operation", "division" },
                    { "numerator", 10 },
                    { "denominator", 0 }
                });
                Console.WriteLine($"   Exception captured: {eventId}");
            }

            // Example 2: Capture message
            Console.WriteLine("\n2. Capturing info message...");
            var messageId = sentry.CaptureMessage(
                "User completed onboarding flow",
                SentryLevel.Info,
                new Dictionary<string, object>
                {
                    { "stepsCompleted", 5 },
                    { "timeTakenSeconds", 120 }
                }
            );
            Console.WriteLine($"   Message captured: {messageId}");

            // Example 3: Use example service
            Console.WriteLine("\n3. Using example service...");
            var service = new ExampleService();
            try
            {
                var data = service.FetchData("123");
                Console.WriteLine($"   Data fetched: {data}");
            }
            catch (Exception)
            {
                Console.WriteLine("   Error handled");
            }

            // Example 4: Transaction with service
            Console.WriteLine("\n4. Processing batch with transaction...");
            var processed = await service.ProcessBatchAsync(new[] { "a", "b", "c" });
            Console.WriteLine($"   Processed {processed} items");

            // Example 5: Scoped context
            Console.WriteLine("\n5. Using scoped context...");
            using (SentrySdk.PushScope())
            {
                SentrySdk.ConfigureScope(scope =>
                {
                    scope.SetTag("feature", "new_checkout");
                    scope.SetExtra("cartItems", 3);
                    scope.SetExtra("totalAmount", 99.99);
                });

                SentrySdk.CaptureMessage("Checkout initiated", SentryLevel.Info);
            }
            Console.WriteLine("   Scoped message captured");

            // Example 6: Manual transaction with spans
            Console.WriteLine("\n6. Creating transaction with spans...");
            sentry.WithTransaction("order_processing", "task", transaction =>
            {
                var fetchSpan = transaction.StartChild("db.query", "Fetch order");
                Task.Delay(50).Wait();
                fetchSpan.Status = SpanStatus.Ok;
                fetchSpan.Finish();

                var paymentSpan = transaction.StartChild("http.client", "Payment API");
                Task.Delay(100).Wait();
                paymentSpan.Status = SpanStatus.Ok;
                paymentSpan.Finish();

                var updateSpan = transaction.StartChild("db.query", "Update order status");
                Task.Delay(50).Wait();
                updateSpan.Status = SpanStatus.Ok;
                updateSpan.Finish();

                return true;
            });
            Console.WriteLine("   Transaction with spans recorded");

            // Clean up
            sentry.ClearUser();

            Console.WriteLine("\n" + new string('=', 60));
            Console.WriteLine("All examples completed!");
            Console.WriteLine("Check your Bugsink dashboard");
            Console.WriteLine(new string('=', 60));

            // Flush events before exit
            await sentry.FlushAsync(TimeSpan.FromSeconds(5));
        }
    }
}
