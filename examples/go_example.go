/*
Bugsink/Sentry SDK Integration Example for Go
==============================================

This example demonstrates comprehensive error tracking integration
using the Sentry SDK with a self-hosted Bugsink server.

Requirements:

	go get github.com/getsentry/sentry-go

DSN Format:

	https://<project-key>@<your-bugsink-host>/<project-id>
*/
package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"net/http"
	"os"
	"runtime"
	"strings"
	"time"

	"github.com/getsentry/sentry-go"
	sentryhttp "github.com/getsentry/sentry-go/http"
)

// =============================================================================
// CONFIGURATION
// =============================================================================

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

var (
	SentryDSN   = getEnv("SENTRY_DSN", "https://your-project-key@errors.observability.app.bauer-group.com/1")
	Environment = getEnv("ENVIRONMENT", "development")
	Release     = getEnv("APP_VERSION", "1.0.0")
	ServerName  = getEnv("HOSTNAME", "")
)

// =============================================================================
// SENTRY SERVICE
// =============================================================================

// SentryService provides a wrapper around the Sentry SDK
type SentryService struct {
	initialized bool
}

// NewSentryService creates a new SentryService instance
func NewSentryService() *SentryService {
	return &SentryService{}
}

// Init initializes the Sentry SDK
func (s *SentryService) Init() error {
	if s.initialized {
		log.Println("Sentry already initialized")
		return nil
	}

	// Determine sample rate based on environment
	tracesSampleRate := 1.0
	if Environment == "production" {
		tracesSampleRate = 0.1
	}

	err := sentry.Init(sentry.ClientOptions{
		Dsn:              SentryDSN,
		Environment:      Environment,
		Release:          fmt.Sprintf("my-app@%s", Release),
		ServerName:       ServerName,
		Debug:            Environment == "development",
		AttachStacktrace: true,

		// Performance Monitoring
		TracesSampleRate: tracesSampleRate,
		ProfilesSampleRate: 0.1,

		// Error Sampling
		SampleRate: 1.0,

		// Before Send Hook
		BeforeSend: beforeSendHandler,

		// Before Breadcrumb Hook
		BeforeBreadcrumb: beforeBreadcrumbHandler,
	})

	if err != nil {
		return fmt.Errorf("sentry initialization failed: %w", err)
	}

	// Set global tags
	sentry.ConfigureScope(func(scope *sentry.Scope) {
		scope.SetTag("app.component", "backend")
		scope.SetTag("app.runtime", "go")
		scope.SetTag("app.go_version", runtime.Version())
	})

	s.initialized = true
	log.Printf("Sentry initialized for environment: %s", Environment)

	return nil
}

// beforeSendHandler processes events before sending
func beforeSendHandler(event *sentry.Event, hint *sentry.EventHint) *sentry.Event {
	// Sanitize sensitive headers
	if event.Request != nil && event.Request.Headers != nil {
		sensitiveHeaders := []string{"Authorization", "Cookie", "X-API-Key"}
		for _, header := range sensitiveHeaders {
			if _, ok := event.Request.Headers[header]; ok {
				event.Request.Headers[header] = "[REDACTED]"
			}
		}
	}

	// Filter specific exceptions
	if hint.OriginalException != nil {
		var expectedErr *ExpectedBusinessError
		if errors.As(hint.OriginalException, &expectedErr) {
			return nil // Don't send this event
		}
	}

	return event
}

// beforeBreadcrumbHandler processes breadcrumbs before adding
func beforeBreadcrumbHandler(breadcrumb *sentry.Breadcrumb, hint *sentry.BreadcrumbHint) *sentry.Breadcrumb {
	// Filter health check requests
	if breadcrumb.Category == "http" {
		if url, ok := breadcrumb.Data["url"].(string); ok {
			if strings.Contains(url, "/health") {
				return nil
			}
		}
	}

	return breadcrumb
}

// SetUser sets the user context
func (s *SentryService) SetUser(id, email, username, ipAddress string, extra map[string]string) {
	sentry.ConfigureScope(func(scope *sentry.Scope) {
		user := sentry.User{
			ID:        id,
			Email:     email,
			Username:  username,
			IPAddress: ipAddress,
		}
		if extra != nil {
			user.Data = extra
		}
		scope.SetUser(user)
	})
}

// ClearUser clears the user context
func (s *SentryService) ClearUser() {
	sentry.ConfigureScope(func(scope *sentry.Scope) {
		scope.SetUser(sentry.User{})
	})
}

// AddBreadcrumb adds a breadcrumb
func (s *SentryService) AddBreadcrumb(message, category string, level sentry.Level, data map[string]interface{}) {
	if category == "" {
		category = "custom"
	}
	if level == "" {
		level = sentry.LevelInfo
	}

	sentry.AddBreadcrumb(&sentry.Breadcrumb{
		Message:   message,
		Category:  category,
		Level:     level,
		Data:      data,
		Timestamp: time.Now(),
	})
}

// SetTag sets a tag
func (s *SentryService) SetTag(key, value string) {
	sentry.ConfigureScope(func(scope *sentry.Scope) {
		scope.SetTag(key, value)
	})
}

// SetExtra sets extra context
func (s *SentryService) SetExtra(key string, value interface{}) {
	sentry.ConfigureScope(func(scope *sentry.Scope) {
		scope.SetExtra(key, value)
	})
}

// SetContext sets custom context
func (s *SentryService) SetContext(name string, data map[string]interface{}) {
	sentry.ConfigureScope(func(scope *sentry.Scope) {
		scope.SetContext(name, data)
	})
}

// CaptureException captures an exception
func (s *SentryService) CaptureException(err error) *sentry.EventID {
	return sentry.CaptureException(err)
}

// CaptureExceptionWithContext captures an exception with extra context
func (s *SentryService) CaptureExceptionWithContext(err error, extraContext map[string]interface{}) *sentry.EventID {
	sentry.WithScope(func(scope *sentry.Scope) {
		for key, value := range extraContext {
			scope.SetExtra(key, value)
		}
		sentry.CaptureException(err)
	})
	return nil
}

// CaptureMessage captures a message
func (s *SentryService) CaptureMessage(message string, level sentry.Level) *sentry.EventID {
	return sentry.CaptureMessage(message)
}

// CaptureMessageWithContext captures a message with extra context
func (s *SentryService) CaptureMessageWithContext(message string, level sentry.Level, extraContext map[string]interface{}) *sentry.EventID {
	var eventID *sentry.EventID
	sentry.WithScope(func(scope *sentry.Scope) {
		scope.SetLevel(level)
		for key, value := range extraContext {
			scope.SetExtra(key, value)
		}
		eventID = sentry.CaptureMessage(message)
	})
	return eventID
}

// WithTransaction executes a function within a transaction
func (s *SentryService) WithTransaction(ctx context.Context, name, operation string, fn func(context.Context, *sentry.Span) error) error {
	span := sentry.StartSpan(ctx, operation, sentry.WithTransactionName(name))
	defer span.Finish()

	err := fn(span.Context(), span)
	if err != nil {
		span.Status = sentry.SpanStatusInternalError
		return err
	}

	span.Status = sentry.SpanStatusOK
	return nil
}

// WithSpan executes a function within a child span
func (s *SentryService) WithSpan(ctx context.Context, operation, description string, fn func(context.Context) error) error {
	span := sentry.StartSpan(ctx, operation, sentry.WithDescription(description))
	defer span.Finish()

	err := fn(span.Context())
	if err != nil {
		span.Status = sentry.SpanStatusInternalError
		return err
	}

	span.Status = sentry.SpanStatusOK
	return nil
}

// Flush flushes pending events
func (s *SentryService) Flush(timeout time.Duration) bool {
	return sentry.Flush(timeout)
}

// =============================================================================
// CUSTOM ERRORS
// =============================================================================

// ExpectedBusinessError represents an expected business logic error
type ExpectedBusinessError struct {
	Message string
}

func (e *ExpectedBusinessError) Error() string {
	return e.Message
}

// =============================================================================
// EXAMPLE SERVICE
// =============================================================================

// ExampleService demonstrates Sentry integration patterns
type ExampleService struct {
	sentry *SentryService
}

// NewExampleService creates a new ExampleService
func NewExampleService(sentry *SentryService) *ExampleService {
	return &ExampleService{sentry: sentry}
}

// FetchData fetches data with error tracking
func (s *ExampleService) FetchData(id string) (string, error) {
	s.sentry.AddBreadcrumb(
		fmt.Sprintf("Fetching data for %s", id),
		"service",
		sentry.LevelInfo,
		map[string]interface{}{"id": id},
	)

	if id == "error" {
		return "", errors.New("failed to fetch data")
	}

	return fmt.Sprintf("Data for %s", id), nil
}

// ProcessBatch processes items with transaction tracking
func (s *ExampleService) ProcessBatch(ctx context.Context, items []string) (int, error) {
	var processed int

	err := s.sentry.WithTransaction(ctx, "process_batch", "task", func(ctx context.Context, span *sentry.Span) error {
		for _, item := range items {
			err := s.sentry.WithSpan(ctx, "task.item", fmt.Sprintf("process_%s", item), func(ctx context.Context) error {
				time.Sleep(50 * time.Millisecond) // Simulate work
				processed++
				return nil
			})
			if err != nil {
				return err
			}
		}
		return nil
	})

	return processed, err
}

// =============================================================================
// HTTP HANDLER EXAMPLE
// =============================================================================

// CreateHTTPHandler creates an HTTP handler with Sentry integration
func CreateHTTPHandler(sentryService *SentryService) http.Handler {
	mux := http.NewServeMux()

	// Create Sentry handler wrapper
	sentryHandler := sentryhttp.New(sentryhttp.Options{
		Repanic: true,
	})

	// Routes
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		sentryService.AddBreadcrumb("Homepage visited", "navigation", sentry.LevelInfo, nil)

		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status": "ok"}`))
	})

	mux.HandleFunc("/api/users/", func(w http.ResponseWriter, r *http.Request) {
		userID := strings.TrimPrefix(r.URL.Path, "/api/users/")

		sentryService.AddBreadcrumb(
			fmt.Sprintf("Fetching user %s", userID),
			"api",
			sentry.LevelInfo,
			map[string]interface{}{"userID": userID},
		)

		if userID == "0" {
			panic("Invalid user ID")
		}

		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(fmt.Sprintf(`{"userID": "%s", "name": "Test User"}`, userID)))
	})

	mux.HandleFunc("/api/error", func(w http.ResponseWriter, r *http.Request) {
		panic("Test error from /api/error endpoint")
	})

	mux.HandleFunc("/api/message", func(w http.ResponseWriter, r *http.Request) {
		sentryService.CaptureMessageWithContext(
			"User triggered test message",
			sentry.LevelInfo,
			map[string]interface{}{
				"endpoint": "/api/message",
				"test":     true,
			},
		)

		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status": "message sent"}`))
	})

	// Wrap with Sentry handler
	return sentryHandler.Handle(mux)
}

// =============================================================================
// MAIN EXAMPLE
// =============================================================================

func main() {
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("Bugsink/Sentry Go SDK Integration Example")
	fmt.Println(strings.Repeat("=", 60))

	// Initialize Sentry
	sentryService := NewSentryService()
	if err := sentryService.Init(); err != nil {
		log.Fatalf("Failed to initialize Sentry: %v", err)
	}
	defer sentryService.Flush(5 * time.Second)

	// Set user context
	sentryService.SetUser(
		"user-123",
		"developer@example.com",
		"developer",
		"127.0.0.1",
		map[string]string{"subscriptionTier": "premium"},
	)

	// Add breadcrumbs
	sentryService.AddBreadcrumb("Application started", "app", sentry.LevelInfo, nil)
	sentryService.AddBreadcrumb("User authenticated", "auth", sentry.LevelInfo, nil)

	// Example 1: Capture handled exception
	fmt.Println("\n1. Capturing handled exception...")
	func() {
		defer func() {
			if r := recover(); r != nil {
				err := fmt.Errorf("panic: %v", r)
				eventID := sentryService.CaptureExceptionWithContext(err, map[string]interface{}{
					"operation": "division",
					"numerator": 10,
					"denominator": 0,
				})
				fmt.Printf("   Exception captured: %v\n", eventID)
			}
		}()

		// This will panic
		result := 10 / 0
		_ = result
	}()

	// Example 2: Capture message
	fmt.Println("\n2. Capturing info message...")
	eventID := sentryService.CaptureMessageWithContext(
		"User completed onboarding flow",
		sentry.LevelInfo,
		map[string]interface{}{
			"stepsCompleted":    5,
			"timeTakenSeconds": 120,
		},
	)
	fmt.Printf("   Message captured: %v\n", eventID)

	// Example 3: Use example service
	fmt.Println("\n3. Using example service...")
	service := NewExampleService(sentryService)
	data, err := service.FetchData("123")
	if err != nil {
		fmt.Println("   Error handled")
	} else {
		fmt.Printf("   Data fetched: %s\n", data)
	}

	// Example 4: Transaction with service
	fmt.Println("\n4. Processing batch with transaction...")
	ctx := context.Background()
	processed, err := service.ProcessBatch(ctx, []string{"a", "b", "c"})
	if err != nil {
		fmt.Printf("   Error: %v\n", err)
	} else {
		fmt.Printf("   Processed %d items\n", processed)
	}

	// Example 5: Scoped context
	fmt.Println("\n5. Using scoped context...")
	sentry.WithScope(func(scope *sentry.Scope) {
		scope.SetTag("feature", "new_checkout")
		scope.SetExtra("cartItems", 3)
		scope.SetExtra("totalAmount", 99.99)

		sentry.CaptureMessage("Checkout initiated")
	})
	fmt.Println("   Scoped message captured")

	// Example 6: Manual transaction with spans
	fmt.Println("\n6. Creating transaction with spans...")
	sentryService.WithTransaction(ctx, "order_processing", "task", func(ctx context.Context, txn *sentry.Span) error {
		// Fetch order
		fetchSpan := sentry.StartSpan(ctx, "db.query", sentry.WithDescription("Fetch order"))
		time.Sleep(50 * time.Millisecond)
		fetchSpan.Status = sentry.SpanStatusOK
		fetchSpan.Finish()

		// Payment API
		paymentSpan := sentry.StartSpan(ctx, "http.client", sentry.WithDescription("Payment API"))
		time.Sleep(100 * time.Millisecond)
		paymentSpan.Status = sentry.SpanStatusOK
		paymentSpan.Finish()

		// Update order status
		updateSpan := sentry.StartSpan(ctx, "db.query", sentry.WithDescription("Update order status"))
		time.Sleep(50 * time.Millisecond)
		updateSpan.Status = sentry.SpanStatusOK
		updateSpan.Finish()

		return nil
	})
	fmt.Println("   Transaction with spans recorded")

	// Clean up
	sentryService.ClearUser()

	fmt.Println("\n" + strings.Repeat("=", 60))
	fmt.Println("All examples completed!")
	fmt.Println("Check your Bugsink dashboard")
	fmt.Println(strings.Repeat("=", 60))
}
