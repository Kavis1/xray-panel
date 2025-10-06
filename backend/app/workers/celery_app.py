from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "xray_panel",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=20 * 60,
)

celery_app.conf.beat_schedule = {
    "collect-node-stats": {
        "task": "app.workers.tasks.collect_node_stats",
        "schedule": 60.0,  # Every minute
    },
    "collect-user-traffic-stats": {
        "task": "app.workers.tasks.collect_user_traffic_stats",
        "schedule": 300.0,  # Every 5 minutes - collect traffic from all nodes
    },
    "check-user-connection-limits": {
        "task": "app.workers.tasks.check_user_connection_limits",
        "schedule": 180.0,  # Every 3 minutes - check connection limits
    },
    "check-user-expiration": {
        "task": "app.workers.tasks.check_user_expiration",
        "schedule": 300.0,  # Every 5 minutes
    },
    "check-traffic-limits": {
        "task": "app.workers.tasks.check_traffic_limits",
        "schedule": 60.0,  # Every minute
    },
    "process-webhook-queue": {
        "task": "app.workers.tasks.process_webhook_queue",
        "schedule": settings.JOB_SEND_NOTIFICATIONS_INTERVAL,
    },
    "reset-periodic-traffic": {
        "task": "app.workers.tasks.reset_periodic_traffic",
        "schedule": 3600.0,  # Every hour
    },
}
