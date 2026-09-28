"""
Synthetic historical incident data for seeding Hindsight memory.

30+ realistic incidents with recurring patterns across multiple services.
Includes a deliberate cluster of deployment-related payments-api incidents
for clear before/after demo demonstration.
"""

from datetime import datetime, timezone
from backend.memory.memory_types import (
    Incident, IncidentMetrics, AttemptedAction,
    ActionResult, Severity, IncidentStatus
)


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


SYNTHETIC_INCIDENTS: list[Incident] = [

    # ── DEMO CLUSTER ── deployment-related payments-api incidents ────────────
    Incident(
        incident_id="INC-017",
        timestamp=_dt("2026-08-12T14:22:00"),
        service="payments-api",
        environment="production",
        severity=Severity.SEV1,
        status=IncidentStatus.RESOLVED,
        symptoms=[
            "API latency increased from 240ms to 2100ms (p95)",
            "HTTP 500 errors increased to 16%",
            "Payment processing timeout rate up 300%",
        ],
        metrics=IncidentMetrics(
            latency_ms=2100, error_rate=0.16,
            cpu_percent=72, memory_percent=61,
            db_cpu_percent=38, db_connections=45
        ),
        recent_changes=["payments-api v2.3.1 deployed 8 minutes before incident"],
        hypotheses=[
            "Bad deployment introduced a bug",
            "Database connection exhaustion",
            "Network degradation between service and database",
        ],
        attempted_actions=[
            AttemptedAction(action="Restart service pods", result=ActionResult.FAILED,
                            notes="Latency remained high after restart"),
            AttemptedAction(action="Increase database connection pool size", result=ActionResult.FAILED,
                            notes="DB connections were not exhausted, no improvement"),
            AttemptedAction(action="Rollback deployment to v2.3.0", result=ActionResult.SUCCESS,
                            notes="Latency dropped to normal within 90 seconds"),
        ],
        root_cause="Bad deployment — v2.3.1 introduced an inefficient synchronous lock in payment processing",
        successful_resolution="Rollback deployment to previous version (v2.3.0)",
        resolution_time_minutes=12,
        lessons_learned=[
            "The recent deployment was the key signal — correlate deploy time with incident start",
            "Database metrics were normal throughout — DB was not the cause",
            "Restarting pods did not help because the bug was in the code, not state",
            "Increasing DB connection pool had no effect and wasted time",
            "Rollback resolved the incident immediately",
        ],
        memory_retained=True,
    ),

    Incident(
        incident_id="INC-031",
        timestamp=_dt("2026-08-28T09:05:00"),
        service="payments-api",
        environment="production",
        severity=Severity.SEV1,
        status=IncidentStatus.RESOLVED,
        symptoms=[
            "API latency spiked from 220ms to 1900ms (p95)",
            "HTTP 500 error rate increased to 19%",
            "Customer payment failures reported via support tickets",
        ],
        metrics=IncidentMetrics(
            latency_ms=1900, error_rate=0.19,
            cpu_percent=68, memory_percent=58,
            db_cpu_percent=42, db_connections=51
        ),
        recent_changes=["payments-api v2.4.0 deployed 11 minutes before incident"],
        hypotheses=[
            "Deployment introduced regression",
            "Database slow queries",
            "Upstream payment gateway issue",
        ],
        attempted_actions=[
            AttemptedAction(action="Restart application servers", result=ActionResult.FAILED,
                            notes="Error rate unchanged after restart"),
            AttemptedAction(action="Inspect database slow query log", result=ActionResult.NOT_APPLICABLE,
                            notes="No slow queries detected, DB performance normal"),
            AttemptedAction(action="Check upstream payment gateway status", result=ActionResult.NOT_APPLICABLE,
                            notes="Gateway status page shows all systems operational"),
            AttemptedAction(action="Rollback deployment to v2.3.9", result=ActionResult.SUCCESS,
                            notes="Errors dropped to baseline within 2 minutes of rollback"),
        ],
        root_cause="Bad deployment — v2.4.0 had a serialization bug in the payment request handler",
        successful_resolution="Rollback to v2.3.9",
        resolution_time_minutes=18,
        lessons_learned=[
            "Second incident in 16 days with identical pattern: deployment → latency spike → rollback resolves",
            "Database CPU was normal — do not investigate DB when deploy is recent and DB looks fine",
            "Restarting application did not help — the issue was code logic, not process state",
            "Payment gateway checks wasted 3 minutes — gateway was fine",
            "Rollback should be first action when a recent deployment coincides with a latency spike",
        ],
        memory_retained=True,
    ),

    Incident(
        incident_id="INC-036",
        timestamp=_dt("2026-09-04T16:45:00"),
        service="payments-api",
        environment="production",
        severity=Severity.SEV2,
        status=IncidentStatus.RESOLVED,
        symptoms=[
            "API latency increased from 230ms to 1800ms (p95)",
            "HTTP 500 errors increased to 12%",
            "Some transactions completing slowly, others failing",
        ],
        metrics=IncidentMetrics(
            latency_ms=1800, error_rate=0.12,
            cpu_percent=55, memory_percent=52,
            db_cpu_percent=91, db_connections=78
        ),
        recent_changes=[],  # No recent deployment
        hypotheses=[
            "Slow database query consuming excessive CPU",
            "Database connection exhaustion",
            "Background job competing for resources",
        ],
        attempted_actions=[
            AttemptedAction(action="Identify slow queries in database", result=ActionResult.SUCCESS,
                            notes="Found a missing index on transactions.customer_id after recent data growth"),
            AttemptedAction(action="Add index on transactions.customer_id", result=ActionResult.SUCCESS,
                            notes="Database CPU dropped from 91% to 28% within minutes"),
        ],
        root_cause="Slow database query — missing index on high-volume table, exposed by data growth",
        successful_resolution="Added database index on transactions.customer_id",
        resolution_time_minutes=25,
        lessons_learned=[
            "Database CPU was the distinguishing signal — 91% is very different from normal (40-50%)",
            "No recent deployment — rule out deployment-related causes",
            "Always check slow query log when DB CPU is high",
            "Data growth can expose missing indexes that were not a problem at lower volume",
        ],
        memory_retained=True,
    ),

    # ── AUTH SERVICE INCIDENTS ───────────────────────────────────────────────
    Incident(
        incident_id="INC-003",
        timestamp=_dt("2026-07-02T10:30:00"),
        service="auth-service",
        environment="production",
        severity=Severity.SEV1,
        status=IncidentStatus.RESOLVED,
        symptoms=[
            "Login requests failing with 401 errors",
            "JWT token validation failures",
            "Users being logged out unexpectedly",
        ],
        metrics=IncidentMetrics(
            latency_ms=120, error_rate=0.95,
            cpu_percent=25, memory_percent=30,
            db_cpu_percent=15
        ),
        recent_changes=["TLS certificate renewed last night"],
        hypotheses=["Expired signing key", "Certificate issue", "Configuration change"],
        attempted_actions=[
            AttemptedAction(action="Check service health endpoint", result=ActionResult.NOT_APPLICABLE),
            AttemptedAction(action="Inspect JWT signing key expiration", result=ActionResult.SUCCESS,
                            notes="Found: JWT signing key expired at midnight"),
            AttemptedAction(action="Rotate JWT signing key", result=ActionResult.SUCCESS),
        ],
        root_cause="Expired JWT signing credentials",
        successful_resolution="Rotate JWT signing key and update configuration",
        resolution_time_minutes=22,
        lessons_learned=[
            "Monitor credential expiration dates with alerts 30 days in advance",
            "JWT signing key expiration causes near-100% error rate, not partial failures",
        ],
        memory_retained=True,
    ),

    Incident(
        incident_id="INC-008",
        timestamp=_dt("2026-07-15T03:15:00"),
        service="auth-service",
        environment="production",
        severity=Severity.SEV2,
        status=IncidentStatus.RESOLVED,
        symptoms=[
            "Intermittent login failures (15% of requests)",
            "High latency on token validation",
            "Redis cache connection errors in logs",
        ],
        metrics=IncidentMetrics(
            latency_ms=890, error_rate=0.15,
            cpu_percent=45, memory_percent=55,
            db_cpu_percent=20
        ),
        recent_changes=["Redis cluster maintenance window completed 2 hours ago"],
        hypotheses=["Redis cache failure", "Session store corruption", "Network issue"],
        attempted_actions=[
            AttemptedAction(action="Check Redis cluster health", result=ActionResult.SUCCESS,
                            notes="Found: one Redis replica failed to rejoin after maintenance"),
            AttemptedAction(action="Force Redis replica resync", result=ActionResult.SUCCESS),
        ],
        root_cause="Cache failure — Redis replica did not rejoin cluster after maintenance",
        successful_resolution="Force Redis replica resync",
        resolution_time_minutes=35,
        lessons_learned=[
            "Always verify cache cluster health after maintenance windows",
            "Redis failure causes intermittent auth failures, not total outage",
        ],
        memory_retained=True,
    ),

    # ── CHECKOUT SERVICE INCIDENTS ───────────────────────────────────────────
    Incident(
        incident_id="INC-011",
        timestamp=_dt("2026-07-20T11:00:00"),
        service="checkout-service",
        environment="production",
        severity=Severity.SEV1,
        status=IncidentStatus.RESOLVED,
        symptoms=[
            "Checkout requests timing out",
            "Memory usage growing unbounded",
            "OOMKilled pods every 15 minutes",
        ],
        metrics=IncidentMetrics(
            latency_ms=5000, error_rate=0.35,
            cpu_percent=80, memory_percent=98,
            db_cpu_percent=40
        ),
        recent_changes=["checkout-service v1.8.2 deployed 2 days ago"],
        hypotheses=["Memory leak in new version", "Session data accumulation", "Cache not expiring"],
        attempted_actions=[
            AttemptedAction(action="Increase pod memory limit", result=ActionResult.PARTIAL,
                            notes="Reduced OOMKill frequency but did not solve the leak"),
            AttemptedAction(action="Profile memory usage", result=ActionResult.SUCCESS,
                            notes="Found unbounded session cache in v1.8.2"),
            AttemptedAction(action="Rollback to v1.8.1", result=ActionResult.SUCCESS),
        ],
        root_cause="Memory leak — v1.8.2 introduced an unbounded session cache",
        successful_resolution="Rollback to v1.8.1",
        resolution_time_minutes=45,
        lessons_learned=[
            "Memory growing to 98% with OOMKilled pods is a clear memory leak signal",
            "Increasing memory limits only delays the inevitable — find the root cause",
            "Memory leaks often appear days after deployment as memory accumulates",
        ],
        memory_retained=True,
    ),

    Incident(
        incident_id="INC-019",
        timestamp=_dt("2026-08-14T14:30:00"),
        service="checkout-service",
        environment="production",
        severity=Severity.SEV2,
        status=IncidentStatus.RESOLVED,
        symptoms=[
            "Checkout API latency increased 200%",
            "Stripe payment integration returning timeouts",
            "Error logs show connection refused from Stripe",
        ],
        metrics=IncidentMetrics(
            latency_ms=3200, error_rate=0.28, cpu_percent=40, memory_percent=45),
        recent_changes=[],
        hypotheses=["Third-party payment API outage", "Network routing issue", "SSL certificate issue"],
        attempted_actions=[
            AttemptedAction(action="Check Stripe status page", result=ActionResult.SUCCESS,
                            notes="Stripe degraded performance incident active"),
            AttemptedAction(action="Implement checkout request queuing", result=ActionResult.PARTIAL),
            AttemptedAction(action="Wait for Stripe recovery", result=ActionResult.SUCCESS),
        ],
        root_cause="Third-party API outage — Stripe experiencing degraded performance",
        successful_resolution="Waited for Stripe to resolve their incident",
        resolution_time_minutes=67,
        lessons_learned=[
            "Always check third-party status pages before investigating internal causes",
            "Implement circuit breakers for critical external dependencies",
        ],
        memory_retained=True,
    ),

    # ── ORDERS API INCIDENTS ─────────────────────────────────────────────────
    Incident(
        incident_id="INC-005",
        timestamp=_dt("2026-07-08T08:45:00"),
        service="orders-api",
        environment="production",
        severity=Severity.SEV2,
        status=IncidentStatus.RESOLVED,
        symptoms=[
            "Order creation requests failing",
            "Database connection pool exhausted",
            "Connection timeout errors in logs",
        ],
        metrics=IncidentMetrics(
            latency_ms=4500, error_rate=0.42,
            cpu_percent=35, memory_percent=40,
            db_cpu_percent=55, db_connections=200
        ),
        recent_changes=["New bulk order import feature enabled"],
        hypotheses=["DB connection pool exhaustion", "Long-running transactions", "Connection leak"],
        attempted_actions=[
            AttemptedAction(action="Check active database connections", result=ActionResult.SUCCESS,
                            notes="200 connections open, all held by bulk import jobs"),
            AttemptedAction(action="Kill long-running bulk import queries", result=ActionResult.SUCCESS),
            AttemptedAction(action="Add connection timeout to bulk import jobs", result=ActionResult.SUCCESS),
        ],
        root_cause="Database connection exhaustion — bulk import feature held connections too long",
        successful_resolution="Kill long-running queries and add connection timeouts",
        resolution_time_minutes=28,
        lessons_learned=[
            "DB connections at max (200) with long-running queries is the classic pool exhaustion pattern",
            "Bulk operations need connection timeouts and should use separate connection pools",
        ],
        memory_retained=True,
    ),

    Incident(
        incident_id="INC-022",
        timestamp=_dt("2026-08-18T13:20:00"),
        service="orders-api",
        environment="production",
        severity=Severity.SEV2,
        status=IncidentStatus.RESOLVED,
        symptoms=[
            "Orders API CPU at 95%",
            "Response times increasing",
            "Order processing queue growing",
        ],
        metrics=IncidentMetrics(
            latency_ms=2100, error_rate=0.08,
            cpu_percent=95, memory_percent=60,
            db_cpu_percent=35
        ),
        recent_changes=["New order recommendation algorithm enabled in A/B test"],
        hypotheses=["CPU-intensive algorithm", "Infinite loop in new code", "Missing caching"],
        attempted_actions=[
            AttemptedAction(action="Profile CPU usage", result=ActionResult.SUCCESS,
                            notes="Recommendation algorithm calling ML model on every request without caching"),
            AttemptedAction(action="Disable A/B test (recommendation feature)", result=ActionResult.SUCCESS),
            AttemptedAction(action="Add caching layer for recommendations", result=ActionResult.SUCCESS),
        ],
        root_cause="CPU saturation — uncached ML inference on every request",
        successful_resolution="Disable feature flag and add caching",
        resolution_time_minutes=20,
        lessons_learned=[
            "CPU at 95% with no corresponding DB issues points to application-level computation",
            "A/B test feature flags can introduce performance regressions in production",
            "ML inference must be cached — per-request inference does not scale",
        ],
        memory_retained=True,
    ),

    # ── INVENTORY SERVICE INCIDENTS ──────────────────────────────────────────
    Incident(
        incident_id="INC-014",
        timestamp=_dt("2026-07-25T17:10:00"),
        service="inventory-service",
        environment="production",
        severity=Severity.SEV3,
        status=IncidentStatus.RESOLVED,
        symptoms=[
            "Inventory lookups returning stale data",
            "Cache hit rate dropped to 0%",
            "Increased database load",
        ],
        metrics=IncidentMetrics(
            latency_ms=850, error_rate=0.02,
            cpu_percent=30, memory_percent=35,
            db_cpu_percent=70
        ),
        recent_changes=["Redis version upgrade completed yesterday"],
        hypotheses=["Cache invalidated by Redis upgrade", "Cache configuration issue", "Eviction policy changed"],
        attempted_actions=[
            AttemptedAction(action="Check Redis key count", result=ActionResult.SUCCESS,
                            notes="Zero keys — all cache data lost during upgrade"),
            AttemptedAction(action="Warm cache by pre-loading inventory data", result=ActionResult.SUCCESS),
        ],
        root_cause="Cache failure — Redis upgrade wiped all cache data (no persistence configured)",
        successful_resolution="Pre-warm cache with inventory data",
        resolution_time_minutes=40,
        lessons_learned=[
            "Always configure Redis persistence before upgrades",
            "Cache invalidation causes DB load spike — use this as an indicator",
            "Cache warm-up procedures should be part of Redis maintenance runbooks",
        ],
        memory_retained=True,
    ),

    Incident(
        incident_id="INC-025",
        timestamp=_dt("2026-08-22T09:55:00"),
        service="inventory-service",
        environment="production",
        severity=Severity.SEV2,
        status=IncidentStatus.RESOLVED,
        symptoms=[
            "API latency increased 400%",
            "Timeout errors for bulk inventory queries",
            "Database slow query log filling up",
        ],
        metrics=IncidentMetrics(
            latency_ms=1800, error_rate=0.20,
            cpu_percent=45, memory_percent=50,
            db_cpu_percent=88, db_connections=65
        ),
        recent_changes=[],
        hypotheses=["Missing database index", "Cartesian join in new query", "Data volume threshold"],
        attempted_actions=[
            AttemptedAction(action="Analyze slow query log", result=ActionResult.SUCCESS,
                            notes="Full table scan on product_variants table (10M rows)"),
            AttemptedAction(action="Add composite index on (product_id, sku_code)", result=ActionResult.SUCCESS),
        ],
        root_cause="Slow database query — full table scan on product_variants due to missing index",
        successful_resolution="Add composite index on product_variants",
        resolution_time_minutes=32,
        lessons_learned=[
            "High DB CPU + slow queries = missing index or unoptimized query",
            "Full table scans become critical at 10M+ rows",
        ],
        memory_retained=True,
    ),

    # ── NOTIFICATION SERVICE INCIDENTS ───────────────────────────────────────
    Incident(
        incident_id="INC-009",
        timestamp=_dt("2026-07-17T11:30:00"),
        service="notification-service",
        environment="production",
        severity=Severity.SEV3,
        status=IncidentStatus.RESOLVED,
        symptoms=[
            "Email notifications not being delivered",
            "Notification queue backing up",
            "SMTP connection refused errors in logs",
        ],
        metrics=IncidentMetrics(latency_ms=200, error_rate=0.85, cpu_percent=20, memory_percent=25),
        recent_changes=["SendGrid API key rotated last week"],
        hypotheses=["Expired API credentials", "SMTP rate limiting", "Queue processor failure"],
        attempted_actions=[
            AttemptedAction(action="Check notification queue depth", result=ActionResult.SUCCESS,
                            notes="50,000 messages queued — processor stopped"),
            AttemptedAction(action="Test SendGrid API key", result=ActionResult.SUCCESS,
                            notes="API key expired — rotation was not applied to production config"),
            AttemptedAction(action="Update production API key configuration", result=ActionResult.SUCCESS),
            AttemptedAction(action="Process backlogged notifications", result=ActionResult.SUCCESS),
        ],
        root_cause="Expired credentials — new SendGrid API key not applied to production",
        successful_resolution="Update API key in production configuration",
        resolution_time_minutes=55,
        lessons_learned=[
            "Credential rotations must be applied to all environments, not just staging",
            "High error rate with low CPU/latency typically indicates an auth/credential issue",
            "Always test API keys after rotation before closing the task",
        ],
        memory_retained=True,
    ),

    Incident(
        incident_id="INC-027",
        timestamp=_dt("2026-08-25T14:00:00"),
        service="notification-service",
        environment="production",
        severity=Severity.SEV2,
        status=IncidentStatus.RESOLVED,
        symptoms=[
            "SMS notifications failing",
            "Twilio API returning 403 errors",
            "Notification retries exhausted",
        ],
        metrics=IncidentMetrics(latency_ms=180, error_rate=0.70, cpu_percent=15, memory_percent=20),
        recent_changes=["Twilio account billing threshold reached"],
        hypotheses=["Billing limit reached", "API key issue", "Account suspended"],
        attempted_actions=[
            AttemptedAction(action="Check Twilio dashboard", result=ActionResult.SUCCESS,
                            notes="Monthly SMS limit reached — service suspended"),
            AttemptedAction(action="Upgrade Twilio plan and add SMS credits", result=ActionResult.SUCCESS),
        ],
        root_cause="Third-party service suspension — Twilio billing limit reached",
        successful_resolution="Upgrade Twilio plan",
        resolution_time_minutes=18,
        lessons_learned=[
            "Set billing alerts well before limits are reached",
            "403 from third-party APIs often means auth/billing issue, not a code bug",
        ],
        memory_retained=True,
    ),

    # ── NETWORK DEGRADATION INCIDENTS ────────────────────────────────────────
    Incident(
        incident_id="INC-016",
        timestamp=_dt("2026-08-01T02:30:00"),
        service="payments-api",
        environment="production",
        severity=Severity.SEV1,
        status=IncidentStatus.RESOLVED,
        symptoms=[
            "All services experiencing elevated latency",
            "Cross-AZ network packet loss detected",
            "Database connections timing out intermittently",
        ],
        metrics=IncidentMetrics(
            latency_ms=3500, error_rate=0.25,
            cpu_percent=40, memory_percent=45,
            db_cpu_percent=30
        ),
        recent_changes=[],
        hypotheses=["Network degradation between AZs", "Cloud provider incident", "DNS issue"],
        attempted_actions=[
            AttemptedAction(action="Check cloud provider status page", result=ActionResult.SUCCESS,
                            notes="AWS us-east-1 AZ interconnect degradation reported"),
            AttemptedAction(action="Route traffic to us-east-2 region", result=ActionResult.SUCCESS),
        ],
        root_cause="Network degradation — AWS availability zone interconnect issue",
        successful_resolution="Route traffic to secondary region",
        resolution_time_minutes=38,
        lessons_learned=[
            "When all services are affected simultaneously, suspect infrastructure/network",
            "Always check cloud provider status before investigating application code",
            "Multi-region routing is essential for AZ-level resilience",
        ],
        memory_retained=True,
    ),

    # ── CONFIGURATION ERROR INCIDENTS ────────────────────────────────────────
    Incident(
        incident_id="INC-029",
        timestamp=_dt("2026-08-27T10:00:00"),
        service="orders-api",
        environment="production",
        severity=Severity.SEV2,
        status=IncidentStatus.RESOLVED,
        symptoms=[
            "Orders API returning 500 errors immediately",
            "No traffic reaching the database",
            "Service logs show database host not found",
        ],
        metrics=IncidentMetrics(latency_ms=50, error_rate=0.99, cpu_percent=10, memory_percent=20),
        recent_changes=["Infrastructure configuration update deployed via Terraform"],
        hypotheses=["Wrong database endpoint in config", "DNS misconfiguration", "Firewall rule change"],
        attempted_actions=[
            AttemptedAction(action="Check database connection string in config", result=ActionResult.SUCCESS,
                            notes="Database hostname pointed to staging environment"),
            AttemptedAction(action="Update configuration to correct production database host", result=ActionResult.SUCCESS),
        ],
        root_cause="Configuration error — production service configured to point to staging database",
        successful_resolution="Correct database hostname in production configuration",
        resolution_time_minutes=15,
        lessons_learned=[
            "Near-100% error rate with very low latency (fast failures) = configuration/connection error",
            "Infrastructure-as-code changes must include configuration validation steps",
            "Separate config validation from deployment steps",
        ],
        memory_retained=True,
    ),

    # ── ADDITIONAL INCIDENTS (making total ~30) ──────────────────────────────
    Incident(
        incident_id="INC-002",
        timestamp=_dt("2026-07-01T20:00:00"),
        service="auth-service",
        environment="production",
        severity=Severity.SEV2,
        status=IncidentStatus.RESOLVED,
        symptoms=["Login slowness", "High auth service CPU"],
        metrics=IncidentMetrics(latency_ms=1200, error_rate=0.05, cpu_percent=90, db_cpu_percent=25),
        recent_changes=["Password hashing algorithm upgraded to Argon2id"],
        hypotheses=["CPU-intensive password hashing", "Brute force attack", "Traffic spike"],
        attempted_actions=[
            AttemptedAction(action="Check for brute force attempts", result=ActionResult.NOT_APPLICABLE),
            AttemptedAction(action="Reduce Argon2id iteration count", result=ActionResult.SUCCESS),
        ],
        root_cause="CPU saturation — Argon2id configured with too many iterations for production load",
        successful_resolution="Tune Argon2id parameters",
        resolution_time_minutes=20,
        lessons_learned=["Benchmark security algorithm parameters before production deployment"],
        memory_retained=True,
    ),

    Incident(
        incident_id="INC-007",
        timestamp=_dt("2026-07-12T15:30:00"),
        service="checkout-service",
        environment="production",
        severity=Severity.SEV2,
        status=IncidentStatus.RESOLVED,
        symptoms=["Checkout API 502 errors", "Upstream connection refused"],
        metrics=IncidentMetrics(latency_ms=100, error_rate=0.60, cpu_percent=15),
        recent_changes=["checkout-service v1.7.5 deployed 20 minutes ago"],
        attempted_actions=[
            AttemptedAction(action="Check service health", result=ActionResult.SUCCESS,
                            notes="Service failing to start due to missing environment variable in new version"),
            AttemptedAction(action="Add missing environment variable", result=ActionResult.FAILED,
                            notes="Variable name typo in deployment manifest"),
            AttemptedAction(action="Rollback deployment to v1.7.4", result=ActionResult.SUCCESS),
        ],
        root_cause="Bad deployment — missing environment variable caused service crash loop",
        successful_resolution="Rollback to v1.7.4",
        resolution_time_minutes=25,
        lessons_learned=["Validate environment variable presence in pre-deployment checks"],
        memory_retained=True,
    ),

    Incident(
        incident_id="INC-013",
        timestamp=_dt("2026-07-22T16:00:00"),
        service="inventory-service",
        environment="production",
        severity=Severity.SEV3,
        status=IncidentStatus.RESOLVED,
        symptoms=["Inventory updates slow", "Write queue growing"],
        metrics=IncidentMetrics(latency_ms=600, error_rate=0.03, cpu_percent=50, db_cpu_percent=75),
        recent_changes=[],
        attempted_actions=[
            AttemptedAction(action="Check for blocking transactions in database", result=ActionResult.SUCCESS,
                            notes="Long-running analytics query blocking writes"),
            AttemptedAction(action="Kill analytics query", result=ActionResult.SUCCESS),
        ],
        root_cause="Long-running analytics query blocking write transactions",
        successful_resolution="Kill blocking query and move analytics to read replica",
        resolution_time_minutes=30,
        lessons_learned=["Analytics queries should run on read replicas, not primary"],
        memory_retained=True,
    ),

    Incident(
        incident_id="INC-020",
        timestamp=_dt("2026-08-16T07:15:00"),
        service="orders-api",
        environment="production",
        severity=Severity.SEV1,
        status=IncidentStatus.RESOLVED,
        symptoms=["Complete orders-api outage", "All requests returning 503"],
        metrics=IncidentMetrics(latency_ms=0, error_rate=1.0, cpu_percent=0),
        recent_changes=["Kubernetes node pool maintenance"],
        attempted_actions=[
            AttemptedAction(action="Check pod status", result=ActionResult.SUCCESS,
                            notes="All pods in Pending state — node pool not ready after maintenance"),
            AttemptedAction(action="Force node pool rotation", result=ActionResult.SUCCESS),
        ],
        root_cause="Infrastructure issue — Kubernetes nodes not recovered after maintenance",
        successful_resolution="Force node pool rotation",
        resolution_time_minutes=22,
        lessons_learned=["Verify node pool health after Kubernetes maintenance windows"],
        memory_retained=True,
    ),

    Incident(
        incident_id="INC-033",
        timestamp=_dt("2026-09-01T12:00:00"),
        service="notification-service",
        environment="production",
        severity=Severity.SEV3,
        status=IncidentStatus.RESOLVED,
        symptoms=["Push notifications delayed by 2+ hours", "Message queue depth growing"],
        metrics=IncidentMetrics(latency_ms=200, error_rate=0.01, cpu_percent=85),
        recent_changes=["notification-service v3.1.0 deployed yesterday"],
        attempted_actions=[
            AttemptedAction(action="Check worker thread count", result=ActionResult.SUCCESS,
                            notes="v3.1.0 reduced worker threads from 20 to 2 in config refactor"),
            AttemptedAction(action="Scale up worker threads to 20", result=ActionResult.SUCCESS),
        ],
        root_cause="Configuration regression in deployment — worker threads reduced to 2",
        successful_resolution="Restore worker thread configuration",
        resolution_time_minutes=15,
        lessons_learned=["Configuration defaults must be explicitly validated in deployment diff reviews"],
        memory_retained=True,
    ),

    Incident(
        incident_id="INC-038",
        timestamp=_dt("2026-09-10T18:30:00"),
        service="payments-api",
        environment="production",
        severity=Severity.SEV1,
        status=IncidentStatus.RESOLVED,
        symptoms=[
            "Payment API latency spike to 2300ms",
            "HTTP 500 errors at 14%",
            "Deployment just completed 6 minutes ago",
        ],
        metrics=IncidentMetrics(
            latency_ms=2300, error_rate=0.14,
            cpu_percent=65, memory_percent=55,
            db_cpu_percent=35, db_connections=42
        ),
        recent_changes=["payments-api v2.4.1 deployed 6 minutes before incident"],
        hypotheses=["Bad deployment", "Database issue", "Upstream service degradation"],
        attempted_actions=[
            AttemptedAction(action="Check database metrics", result=ActionResult.NOT_APPLICABLE,
                            notes="DB CPU 35%, connections 42/200 — all normal"),
            AttemptedAction(action="Rollback deployment to v2.4.0", result=ActionResult.SUCCESS,
                            notes="Latency returned to 220ms within 60 seconds"),
        ],
        root_cause="Bad deployment — v2.4.1 introduced blocking I/O in payment processing path",
        successful_resolution="Rollback to v2.4.0",
        resolution_time_minutes=10,
        lessons_learned=[
            "Third deployment-related payments-api incident — need pre-production load testing",
            "Database metrics were normal — this pattern repeats: deployment + normal DB = rollback first",
            "Rollback as first action when pattern matches historical incidents saves significant time",
        ],
        memory_retained=True,
    ),
]
