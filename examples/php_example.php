<?php
/**
 * Bugsink/Sentry SDK Integration Example for PHP
 * ===============================================
 *
 * This example demonstrates comprehensive error tracking integration
 * using the Sentry SDK with a self-hosted Bugsink server.
 *
 * Requirements:
 *     composer require sentry/sentry
 *     composer require sentry/sentry-laravel  # For Laravel
 *     composer require sentry/sentry-symfony  # For Symfony
 *
 * DSN Format:
 *     https://<project-key>@<your-bugsink-host>/<project-id>
 */

declare(strict_types=1);

namespace BugsinkExample;

use Sentry;
use Sentry\State\Scope;
use Sentry\Tracing\SpanContext;
use Sentry\Tracing\TransactionContext;
use Sentry\Tracing\TransactionSource;
use Sentry\Severity;
use Sentry\Breadcrumb;
use Sentry\EventHint;
use Sentry\Event;
use Sentry\UserDataBag;
use Throwable;
use Exception;

// =============================================================================
// CONFIGURATION
// =============================================================================

class SentryConfig
{
    public static function getDsn(): string
    {
        return getenv('SENTRY_DSN') ?: 'https://your-project-key@errors.observability.app.bauer-group.com/1';
    }

    public static function getEnvironment(): string
    {
        return getenv('APP_ENV') ?: getenv('ENVIRONMENT') ?: 'development';
    }

    public static function getRelease(): string
    {
        return getenv('APP_VERSION') ?: '1.0.0';
    }

    public static function isProduction(): bool
    {
        return self::getEnvironment() === 'production';
    }
}

// =============================================================================
// SENTRY SERVICE
// =============================================================================

/**
 * Singleton service for Sentry operations.
 * Provides comprehensive error tracking and performance monitoring.
 */
class SentryService
{
    private static ?SentryService $instance = null;
    private bool $initialized = false;

    private function __construct()
    {
    }

    public static function getInstance(): self
    {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    /**
     * Initialize Sentry SDK.
     * Call this once at application startup.
     */
    public function init(): void
    {
        if ($this->initialized) {
            echo "Sentry already initialized\n";
            return;
        }

        Sentry\init([
            'dsn' => SentryConfig::getDsn(),
            'environment' => SentryConfig::getEnvironment(),
            'release' => 'my-app@' . SentryConfig::getRelease(),

            // Performance Monitoring
            'traces_sample_rate' => SentryConfig::isProduction() ? 0.1 : 1.0,
            'profiles_sample_rate' => 0.1,

            // Error Sampling
            'sample_rate' => 1.0,

            // Data Handling
            'send_default_pii' => false,
            'max_breadcrumbs' => 50,
            'attach_stacktrace' => true,

            // Before Send Hook
            'before_send' => [$this, 'beforeSendHandler'],

            // Before Breadcrumb Hook
            'before_breadcrumb' => [$this, 'beforeBreadcrumbHandler'],

            // Error Types to capture
            'error_types' => E_ALL,
        ]);

        // Set global tags
        Sentry\configureScope(function (Scope $scope): void {
            $scope->setTag('app.component', 'backend');
            $scope->setTag('app.runtime', 'php');
            $scope->setTag('app.php_version', PHP_VERSION);
        });

        $this->initialized = true;
        echo "Sentry initialized for environment: " . SentryConfig::getEnvironment() . "\n";
    }

    /**
     * Process events before sending.
     */
    public function beforeSendHandler(Event $event, ?EventHint $hint): ?Event
    {
        // Sanitize sensitive headers
        $request = $event->getRequest();
        if ($request !== null) {
            $headers = $request['headers'] ?? [];
            $sensitiveHeaders = ['Authorization', 'Cookie', 'X-API-Key'];

            foreach ($sensitiveHeaders as $header) {
                $headerLower = strtolower($header);
                if (isset($headers[$headerLower])) {
                    $headers[$headerLower] = '[REDACTED]';
                }
            }

            // Note: In real implementation, you'd need to modify the request properly
        }

        // Filter specific exceptions
        if ($hint !== null && $hint->exception instanceof ExpectedBusinessException) {
            return null; // Don't send this event
        }

        return $event;
    }

    /**
     * Process breadcrumbs before adding.
     */
    public function beforeBreadcrumbHandler(Breadcrumb $breadcrumb): ?Breadcrumb
    {
        // Filter health check requests
        if ($breadcrumb->getCategory() === 'http') {
            $data = $breadcrumb->getMetadata();
            $url = $data['url'] ?? '';
            if (strpos($url, '/health') !== false) {
                return null;
            }
        }

        return $breadcrumb;
    }

    /**
     * Set user context.
     */
    public function setUser(
        string $id,
        ?string $email = null,
        ?string $username = null,
        ?string $ipAddress = null,
        array $extra = []
    ): void {
        Sentry\configureScope(function (Scope $scope) use ($id, $email, $username, $ipAddress, $extra): void {
            $userData = new UserDataBag(
                $id,
                $email,
                $ipAddress,
                $username
            );

            // Set additional data
            foreach ($extra as $key => $value) {
                $userData->setMetadata($key, $value);
            }

            $scope->setUser($userData);
        });
    }

    /**
     * Clear user context.
     */
    public function clearUser(): void
    {
        Sentry\configureScope(function (Scope $scope): void {
            $scope->removeUser();
        });
    }

    /**
     * Add a breadcrumb.
     */
    public function addBreadcrumb(
        string $message,
        string $category = 'custom',
        string $level = Breadcrumb::LEVEL_INFO,
        array $data = []
    ): void {
        Sentry\addBreadcrumb(new Breadcrumb(
            $level,
            Breadcrumb::TYPE_DEFAULT,
            $category,
            $message,
            $data
        ));
    }

    /**
     * Set a tag.
     */
    public function setTag(string $key, string $value): void
    {
        Sentry\configureScope(function (Scope $scope) use ($key, $value): void {
            $scope->setTag($key, $value);
        });
    }

    /**
     * Set extra context.
     */
    public function setExtra(string $key, $value): void
    {
        Sentry\configureScope(function (Scope $scope) use ($key, $value): void {
            $scope->setExtra($key, $value);
        });
    }

    /**
     * Set custom context.
     */
    public function setContext(string $name, array $context): void
    {
        Sentry\configureScope(function (Scope $scope) use ($name, $context): void {
            $scope->setContext($name, $context);
        });
    }

    /**
     * Capture an exception.
     */
    public function captureException(Throwable $exception): ?string
    {
        return Sentry\captureException($exception);
    }

    /**
     * Capture an exception with extra context.
     */
    public function captureExceptionWithContext(Throwable $exception, array $extraContext): ?string
    {
        $eventId = null;

        Sentry\withScope(function (Scope $scope) use ($exception, $extraContext, &$eventId): void {
            foreach ($extraContext as $key => $value) {
                $scope->setExtra($key, $value);
            }
            $eventId = Sentry\captureException($exception);
        });

        return $eventId;
    }

    /**
     * Capture a message.
     */
    public function captureMessage(string $message, string $level = Severity::INFO): ?string
    {
        return Sentry\captureMessage($message, Severity::fromError(constant("E_USER_" . strtoupper($level))));
    }

    /**
     * Capture a message with extra context.
     */
    public function captureMessageWithContext(string $message, string $level, array $extraContext): ?string
    {
        $eventId = null;

        Sentry\withScope(function (Scope $scope) use ($message, $level, $extraContext, &$eventId): void {
            foreach ($extraContext as $key => $value) {
                $scope->setExtra($key, $value);
            }
            $eventId = Sentry\captureMessage($message);
        });

        return $eventId;
    }

    /**
     * Execute a callback within a transaction.
     */
    public function withTransaction(string $name, string $operation, callable $callback)
    {
        $transactionContext = new TransactionContext();
        $transactionContext->setName($name);
        $transactionContext->setOp($operation);
        $transactionContext->setSource(TransactionSource::custom());

        $transaction = Sentry\startTransaction($transactionContext);
        Sentry\configureScope(function (Scope $scope) use ($transaction): void {
            $scope->setSpan($transaction);
        });

        try {
            $result = $callback($transaction);
            $transaction->setStatus(\Sentry\Tracing\SpanStatus::ok());
            return $result;
        } catch (Throwable $e) {
            $transaction->setStatus(\Sentry\Tracing\SpanStatus::internalError());
            throw $e;
        } finally {
            $transaction->finish();
        }
    }

    /**
     * Execute a callback within a child span.
     */
    public function withSpan($parent, string $operation, string $description, callable $callback)
    {
        $spanContext = new SpanContext();
        $spanContext->setOp($operation);
        $spanContext->setDescription($description);

        $span = $parent->startChild($spanContext);

        try {
            $result = $callback($span);
            $span->setStatus(\Sentry\Tracing\SpanStatus::ok());
            return $result;
        } catch (Throwable $e) {
            $span->setStatus(\Sentry\Tracing\SpanStatus::internalError());
            throw $e;
        } finally {
            $span->finish();
        }
    }

    /**
     * Flush pending events.
     */
    public function flush(int $timeout = 2): void
    {
        // Flush is handled automatically, but you can force it
        $client = Sentry\SentrySdk::getCurrentHub()->getClient();
        if ($client !== null) {
            $client->flush($timeout);
        }
    }
}

// =============================================================================
// CUSTOM EXCEPTIONS
// =============================================================================

/**
 * Expected business exception that should not be reported.
 */
class ExpectedBusinessException extends Exception
{
}

// =============================================================================
// EXAMPLE SERVICE
// =============================================================================

/**
 * Example service demonstrating Sentry integration patterns.
 */
class ExampleService
{
    private SentryService $sentry;

    public function __construct()
    {
        $this->sentry = SentryService::getInstance();
    }

    /**
     * Example method with error tracking.
     */
    public function fetchData(string $id): string
    {
        $this->sentry->addBreadcrumb(
            "Fetching data for {$id}",
            'service',
            Breadcrumb::LEVEL_INFO,
            ['id' => $id]
        );

        if ($id === 'error') {
            throw new \RuntimeException('Failed to fetch data');
        }

        return "Data for {$id}";
    }

    /**
     * Example method with transaction tracking.
     */
    public function processBatch(array $items): int
    {
        return $this->sentry->withTransaction('process_batch', 'task', function ($transaction) use ($items) {
            $processed = 0;

            foreach ($items as $item) {
                $this->sentry->withSpan($transaction, 'task.item', "process_{$item}", function () use (&$processed) {
                    usleep(50000); // Simulate work (50ms)
                    $processed++;
                });
            }

            return $processed;
        });
    }
}

// =============================================================================
// LARAVEL INTEGRATION EXAMPLE
// =============================================================================

/*
// config/sentry.php
return [
    'dsn' => env('SENTRY_DSN'),
    'release' => env('APP_VERSION', '1.0.0'),
    'environment' => env('APP_ENV', 'production'),
    'traces_sample_rate' => env('SENTRY_TRACES_SAMPLE_RATE', 0.1),
    'profiles_sample_rate' => env('SENTRY_PROFILES_SAMPLE_RATE', 0.1),
    'send_default_pii' => false,
    'max_breadcrumbs' => 50,
];

// app/Http/Middleware/SentryContext.php
namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Sentry\State\Scope;
use function Sentry\configureScope;

class SentryContext
{
    public function handle(Request $request, Closure $next)
    {
        if (auth()->check()) {
            configureScope(function (Scope $scope) {
                $user = auth()->user();
                $scope->setUser([
                    'id' => $user->id,
                    'email' => $user->email,
                    'username' => $user->name,
                ]);
            });
        }

        configureScope(function (Scope $scope) use ($request) {
            $scope->setTag('request_id', $request->header('X-Request-ID', uniqid()));
        });

        return $next($request);
    }
}

// app/Http/Controllers/Api/UserController.php
namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use function Sentry\addBreadcrumb;
use function Sentry\captureException;

class UserController extends Controller
{
    public function show(string $id)
    {
        addBreadcrumb(
            category: 'api',
            message: "Fetching user {$id}",
            metadata: ['user_id' => $id]
        );

        try {
            $user = User::findOrFail($id);
            return response()->json($user);
        } catch (\Exception $e) {
            captureException($e);
            throw $e;
        }
    }
}

// app/Exceptions/Handler.php
namespace App\Exceptions;

use Illuminate\Foundation\Exceptions\Handler as ExceptionHandler;
use Throwable;
use function Sentry\captureException;

class Handler extends ExceptionHandler
{
    public function report(Throwable $e)
    {
        if ($this->shouldReport($e)) {
            captureException($e);
        }

        parent::report($e);
    }
}
*/

// =============================================================================
// SYMFONY INTEGRATION EXAMPLE
// =============================================================================

/*
# config/packages/sentry.yaml
sentry:
    dsn: '%env(SENTRY_DSN)%'
    options:
        environment: '%env(APP_ENV)%'
        release: '%env(APP_VERSION)%'
        traces_sample_rate: 0.1
        send_default_pii: false
        max_breadcrumbs: 50

# src/EventSubscriber/SentrySubscriber.php
namespace App\EventSubscriber;

use Sentry\State\Scope;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Component\HttpKernel\Event\RequestEvent;
use Symfony\Component\HttpKernel\KernelEvents;
use Symfony\Component\Security\Core\Security;
use function Sentry\configureScope;

class SentrySubscriber implements EventSubscriberInterface
{
    private Security $security;

    public function __construct(Security $security)
    {
        $this->security = $security;
    }

    public static function getSubscribedEvents(): array
    {
        return [
            KernelEvents::REQUEST => 'onKernelRequest',
        ];
    }

    public function onKernelRequest(RequestEvent $event): void
    {
        if (!$event->isMainRequest()) {
            return;
        }

        $user = $this->security->getUser();
        if ($user !== null) {
            configureScope(function (Scope $scope) use ($user): void {
                $scope->setUser([
                    'id' => $user->getId(),
                    'email' => $user->getEmail(),
                    'username' => $user->getUsername(),
                ]);
            });
        }
    }
}
*/

// =============================================================================
// MAIN EXAMPLE
// =============================================================================

function main(): void
{
    echo str_repeat('=', 60) . "\n";
    echo "Bugsink/Sentry PHP SDK Integration Example\n";
    echo str_repeat('=', 60) . "\n";

    // Initialize Sentry
    $sentry = SentryService::getInstance();
    $sentry->init();

    // Set user context
    $sentry->setUser(
        'user-123',
        'developer@example.com',
        'developer',
        '127.0.0.1',
        ['subscriptionTier' => 'premium']
    );

    // Add breadcrumbs
    $sentry->addBreadcrumb('Application started', 'app');
    $sentry->addBreadcrumb('User authenticated', 'auth');

    // Example 1: Capture handled exception
    echo "\n1. Capturing handled exception...\n";
    try {
        $result = 10 / 0;
    } catch (Throwable $e) {
        $eventId = $sentry->captureExceptionWithContext($e, [
            'operation' => 'division',
            'numerator' => 10,
            'denominator' => 0,
        ]);
        echo "   Exception captured: {$eventId}\n";
    }

    // Example 2: Capture message
    echo "\n2. Capturing info message...\n";
    $eventId = $sentry->captureMessageWithContext(
        'User completed onboarding flow',
        'info',
        [
            'stepsCompleted' => 5,
            'timeTakenSeconds' => 120,
        ]
    );
    echo "   Message captured: {$eventId}\n";

    // Example 3: Use example service
    echo "\n3. Using example service...\n";
    $service = new ExampleService();
    try {
        $data = $service->fetchData('123');
        echo "   Data fetched: {$data}\n";
    } catch (Throwable $e) {
        echo "   Error handled\n";
    }

    // Example 4: Transaction with service
    echo "\n4. Processing batch with transaction...\n";
    $processed = $service->processBatch(['a', 'b', 'c']);
    echo "   Processed {$processed} items\n";

    // Example 5: Scoped context
    echo "\n5. Using scoped context...\n";
    Sentry\withScope(function (Scope $scope): void {
        $scope->setTag('feature', 'new_checkout');
        $scope->setExtra('cartItems', 3);
        $scope->setExtra('totalAmount', 99.99);

        Sentry\captureMessage('Checkout initiated');
    });
    echo "   Scoped message captured\n";

    // Example 6: Manual transaction with spans
    echo "\n6. Creating transaction with spans...\n";
    $sentry->withTransaction('order_processing', 'task', function ($transaction) use ($sentry) {
        $sentry->withSpan($transaction, 'db.query', 'Fetch order', function () {
            usleep(50000);
        });

        $sentry->withSpan($transaction, 'http.client', 'Payment API', function () {
            usleep(100000);
        });

        $sentry->withSpan($transaction, 'db.query', 'Update order status', function () {
            usleep(50000);
        });

        return true;
    });
    echo "   Transaction with spans recorded\n";

    // Clean up
    $sentry->clearUser();

    echo "\n" . str_repeat('=', 60) . "\n";
    echo "All examples completed!\n";
    echo "Check your Bugsink dashboard\n";
    echo str_repeat('=', 60) . "\n";

    // Flush events before exit
    $sentry->flush(5);
}

// Run if executed directly
if (php_sapi_name() === 'cli' && basename(__FILE__) === basename($_SERVER['PHP_SELF'] ?? '')) {
    // Require autoloader (adjust path as needed)
    // require_once __DIR__ . '/vendor/autoload.php';

    main();
}
