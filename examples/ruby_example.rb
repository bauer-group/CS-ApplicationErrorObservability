# frozen_string_literal: true

#
# Bugsink/Sentry SDK Integration Example for Ruby
# ================================================
#
# This example demonstrates comprehensive error tracking integration
# using the Sentry SDK with a self-hosted Bugsink server.
#
# Requirements:
#     gem install sentry-ruby
#     gem install sentry-rails  # For Rails applications
#
# DSN Format:
#     https://<project-key>@<your-bugsink-host>/<project-id>
#

require 'sentry-ruby'

# =============================================================================
# CONFIGURATION
# =============================================================================

module SentryConfig
  def self.dsn
    ENV.fetch('SENTRY_DSN', 'https://your-project-key@errors.observability.app.bauer-group.com/1')
  end

  def self.environment
    ENV.fetch('RACK_ENV', ENV.fetch('RAILS_ENV', 'development'))
  end

  def self.release
    ENV.fetch('APP_VERSION', '1.0.0')
  end

  def self.production?
    environment == 'production'
  end
end

# =============================================================================
# SENTRY SERVICE
# =============================================================================

# Singleton service for Sentry operations.
# Provides comprehensive error tracking and performance monitoring.
class SentryService
  class << self
    def instance
      @instance ||= new
    end
  end

  def initialize
    @initialized = false
  end

  # Initialize Sentry SDK.
  # Call this once at application startup.
  def init
    if @initialized
      puts 'Sentry already initialized'
      return
    end

    Sentry.init do |config|
      config.dsn = SentryConfig.dsn
      config.environment = SentryConfig.environment
      config.release = "my-app@#{SentryConfig.release}"

      # Performance Monitoring
      config.traces_sample_rate = SentryConfig.production? ? 0.1 : 1.0
      config.profiles_sample_rate = 0.1

      # Error Sampling
      config.sample_rate = 1.0

      # Data Handling
      config.send_default_pii = false
      config.max_breadcrumbs = 50

      # Before Send Hook
      config.before_send = method(:before_send_handler)

      # Before Breadcrumb Hook
      config.before_breadcrumb = method(:before_breadcrumb_handler)

      # Debug mode
      config.debug = !SentryConfig.production?

      # Excluded exceptions
      config.excluded_exceptions += ['ExpectedBusinessError']
    end

    # Set global tags
    Sentry.set_tags(
      'app.component' => 'backend',
      'app.runtime' => 'ruby',
      'app.ruby_version' => RUBY_VERSION
    )

    @initialized = true
    puts "Sentry initialized for environment: #{SentryConfig.environment}"
  end

  # Process events before sending.
  def before_send_handler(event, hint)
    # Sanitize sensitive headers
    if event.request&.headers
      sensitive_headers = %w[Authorization Cookie X-API-Key]
      sensitive_headers.each do |header|
        event.request.headers[header] = '[REDACTED]' if event.request.headers[header]
      end
    end

    # Filter specific exceptions
    if hint[:exception].is_a?(ExpectedBusinessError)
      return nil # Don't send this event
    end

    event
  end

  # Process breadcrumbs before adding.
  def before_breadcrumb_handler(breadcrumb, hint)
    # Filter health check requests
    if breadcrumb.category == 'http'
      url = breadcrumb.data[:url].to_s
      return nil if url.include?('/health')
    end

    breadcrumb
  end

  # Set user context.
  def set_user(id:, email: nil, username: nil, ip_address: nil, **extra)
    Sentry.set_user(
      id: id,
      email: email,
      username: username,
      ip_address: ip_address,
      **extra
    )
  end

  # Clear user context.
  def clear_user
    Sentry.set_user(nil)
  end

  # Add a breadcrumb.
  def add_breadcrumb(message:, category: 'custom', level: :info, data: {})
    Sentry.add_breadcrumb(
      Sentry::Breadcrumb.new(
        message: message,
        category: category,
        level: level,
        data: data,
        timestamp: Time.now.to_i
      )
    )
  end

  # Set a tag.
  def set_tag(key, value)
    Sentry.set_tags(key => value)
  end

  # Set extra context.
  def set_extra(key, value)
    Sentry.set_extras(key => value)
  end

  # Set custom context.
  def set_context(name, context)
    Sentry.set_context(name, context)
  end

  # Capture an exception.
  def capture_exception(exception, **extra_context)
    Sentry.capture_exception(exception, extra: extra_context)
  end

  # Capture a message.
  def capture_message(message, level: :info, **extra_context)
    Sentry.capture_message(message, level: level, extra: extra_context)
  end

  # Execute a block within a transaction.
  def with_transaction(name:, op:)
    transaction = Sentry.start_transaction(name: name, op: op)
    Sentry.configure_scope { |scope| scope.set_span(transaction) }

    begin
      result = yield transaction
      transaction.set_status('ok')
      result
    rescue StandardError => e
      transaction.set_status('internal_error')
      raise
    ensure
      transaction.finish
    end
  end

  # Execute a block within a child span.
  def with_span(transaction, op:, description:)
    span = transaction.start_child(op: op, description: description)

    begin
      result = yield span
      span.set_status('ok')
      result
    rescue StandardError => e
      span.set_status('internal_error')
      raise
    ensure
      span.finish
    end
  end

  # Execute a block within a scope.
  def with_scope
    Sentry.with_scope do |scope|
      yield scope
    end
  end

  # Flush pending events.
  def flush(timeout = 5)
    # Sentry Ruby SDK handles flushing automatically on exit
    # For explicit flush, you can use:
    client = Sentry.get_current_client
    client&.transport&.flush
  end
end

# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

# Expected business exception that should not be reported.
class ExpectedBusinessError < StandardError
end

# =============================================================================
# EXAMPLE SERVICE
# =============================================================================

# Example service demonstrating Sentry integration patterns.
class ExampleService
  def initialize
    @sentry = SentryService.instance
  end

  # Example method with error tracking.
  def fetch_data(id)
    @sentry.add_breadcrumb(
      message: "Fetching data for #{id}",
      category: 'service',
      data: { id: id }
    )

    raise 'Failed to fetch data' if id == 'error'

    "Data for #{id}"
  end

  # Example method with transaction tracking.
  def process_batch(items)
    @sentry.with_transaction(name: 'process_batch', op: 'task') do |transaction|
      processed = 0

      items.each do |item|
        @sentry.with_span(transaction, op: 'task.item', description: "process_#{item}") do
          sleep(0.05) # Simulate work
          processed += 1
        end
      end

      processed
    end
  end
end

# =============================================================================
# RAILS INTEGRATION EXAMPLE
# =============================================================================

=begin
# config/initializers/sentry.rb

Sentry.init do |config|
  config.dsn = ENV['SENTRY_DSN']
  config.environment = Rails.env
  config.release = ENV.fetch('APP_VERSION', '1.0.0')

  # Performance Monitoring
  config.traces_sample_rate = Rails.env.production? ? 0.1 : 1.0
  config.profiles_sample_rate = 0.1

  # Rails-specific settings
  config.breadcrumbs_logger = [:active_support_logger, :http_logger]
  config.send_default_pii = false

  # Exclude common Rails exceptions
  config.excluded_exceptions += [
    'ActionController::RoutingError',
    'ActiveRecord::RecordNotFound'
  ]

  # Before send hook
  config.before_send = lambda do |event, hint|
    # Filter or modify events
    event
  end
end

# app/controllers/application_controller.rb

class ApplicationController < ActionController::Base
  before_action :set_sentry_context

  private

  def set_sentry_context
    return unless current_user

    Sentry.set_user(
      id: current_user.id,
      email: current_user.email,
      username: current_user.name
    )

    Sentry.set_tags(
      request_id: request.request_id,
      ip: request.remote_ip
    )
  end
end

# app/controllers/api/users_controller.rb

class Api::UsersController < ApplicationController
  def show
    Sentry.add_breadcrumb(
      Sentry::Breadcrumb.new(
        category: 'api',
        message: "Fetching user #{params[:id]}"
      )
    )

    @user = User.find(params[:id])
    render json: @user
  rescue ActiveRecord::RecordNotFound => e
    Sentry.capture_exception(e, extra: { user_id: params[:id] })
    render json: { error: 'User not found' }, status: :not_found
  end

  def create
    Sentry.with_scope do |scope|
      scope.set_tag('action', 'create_user')

      @user = User.create!(user_params)
      render json: @user, status: :created
    end
  rescue ActiveRecord::RecordInvalid => e
    Sentry.capture_exception(e)
    render json: { errors: e.record.errors }, status: :unprocessable_entity
  end
end

# app/jobs/process_order_job.rb

class ProcessOrderJob < ApplicationJob
  queue_as :default

  def perform(order_id)
    transaction = Sentry.start_transaction(
      name: 'ProcessOrderJob',
      op: 'job'
    )

    Sentry.configure_scope { |scope| scope.set_span(transaction) }

    begin
      order = Order.find(order_id)

      # Fetch order details
      fetch_span = transaction.start_child(op: 'db.query', description: 'Fetch order')
      order_details = order.details
      fetch_span.finish

      # Process payment
      payment_span = transaction.start_child(op: 'http.client', description: 'Payment API')
      PaymentService.process(order)
      payment_span.finish

      # Update status
      update_span = transaction.start_child(op: 'db.query', description: 'Update status')
      order.update!(status: 'completed')
      update_span.finish

      transaction.set_status('ok')
    rescue => e
      transaction.set_status('internal_error')
      Sentry.capture_exception(e, extra: { order_id: order_id })
      raise
    ensure
      transaction.finish
    end
  end
end

# config/application.rb - Optional: Add middleware

module MyApp
  class Application < Rails::Application
    # Sentry middleware is automatically included with sentry-rails
    # For custom error handling:

    config.middleware.use Sentry::Rails::CaptureExceptions
  end
end
=end

# =============================================================================
# SINATRA INTEGRATION EXAMPLE
# =============================================================================

=begin
# app.rb

require 'sinatra'
require 'sentry-ruby'

# Initialize Sentry
Sentry.init do |config|
  config.dsn = ENV['SENTRY_DSN']
  config.traces_sample_rate = 0.5
end

# Use Sentry middleware
use Sentry::Rack::CaptureExceptions

before do
  Sentry.set_tags(request_id: env['HTTP_X_REQUEST_ID'] || SecureRandom.uuid)
end

get '/' do
  Sentry.add_breadcrumb(
    Sentry::Breadcrumb.new(message: 'Homepage visited')
  )

  { status: 'ok' }.to_json
end

get '/api/users/:id' do
  user_id = params[:id]

  Sentry.add_breadcrumb(
    Sentry::Breadcrumb.new(
      category: 'api',
      message: "Fetching user #{user_id}"
    )
  )

  # Your logic here
  { user_id: user_id, name: 'Test User' }.to_json
end

get '/api/error' do
  raise 'Test error'
end

error do
  error = env['sinatra.error']
  Sentry.capture_exception(error)

  { error: error.message }.to_json
end
=end

# =============================================================================
# MAIN EXAMPLE
# =============================================================================

def main
  puts '=' * 60
  puts 'Bugsink/Sentry Ruby SDK Integration Example'
  puts '=' * 60

  # Initialize Sentry
  sentry = SentryService.instance
  sentry.init

  # Set user context
  sentry.set_user(
    id: 'user-123',
    email: 'developer@example.com',
    username: 'developer',
    subscription_tier: 'premium'
  )

  # Add breadcrumbs
  sentry.add_breadcrumb(message: 'Application started', category: 'app')
  sentry.add_breadcrumb(message: 'User authenticated', category: 'auth')

  # Example 1: Capture handled exception
  puts "\n1. Capturing handled exception..."
  begin
    result = 10 / 0
  rescue ZeroDivisionError => e
    event_id = sentry.capture_exception(
      e,
      operation: 'division',
      numerator: 10,
      denominator: 0
    )
    puts "   Exception captured: #{event_id}"
  end

  # Example 2: Capture message
  puts "\n2. Capturing info message..."
  event_id = sentry.capture_message(
    'User completed onboarding flow',
    level: :info,
    steps_completed: 5,
    time_taken_seconds: 120
  )
  puts "   Message captured: #{event_id}"

  # Example 3: Use example service
  puts "\n3. Using example service..."
  service = ExampleService.new
  begin
    data = service.fetch_data('123')
    puts "   Data fetched: #{data}"
  rescue StandardError
    puts '   Error handled'
  end

  # Example 4: Transaction with service
  puts "\n4. Processing batch with transaction..."
  processed = service.process_batch(%w[a b c])
  puts "   Processed #{processed} items"

  # Example 5: Scoped context
  puts "\n5. Using scoped context..."
  sentry.with_scope do |scope|
    scope.set_tag('feature', 'new_checkout')
    scope.set_extra('cart_items', 3)
    scope.set_extra('total_amount', 99.99)

    Sentry.capture_message('Checkout initiated')
  end
  puts '   Scoped message captured'

  # Example 6: Manual transaction with spans
  puts "\n6. Creating transaction with spans..."
  sentry.with_transaction(name: 'order_processing', op: 'task') do |transaction|
    sentry.with_span(transaction, op: 'db.query', description: 'Fetch order') do
      sleep(0.05)
    end

    sentry.with_span(transaction, op: 'http.client', description: 'Payment API') do
      sleep(0.1)
    end

    sentry.with_span(transaction, op: 'db.query', description: 'Update order status') do
      sleep(0.05)
    end

    true
  end
  puts '   Transaction with spans recorded'

  # Clean up
  sentry.clear_user

  puts "\n" + '=' * 60
  puts 'All examples completed!'
  puts 'Check your Bugsink dashboard'
  puts '=' * 60

  # Flush events before exit
  sentry.flush(5)
end

# Run if executed directly
main if __FILE__ == $PROGRAM_NAME
