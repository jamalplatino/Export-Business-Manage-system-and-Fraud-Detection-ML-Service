import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("export_billing")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "aggregate-daily-revenue-nightly": {
        "task": "dashboard.tasks.aggregate_daily_revenue",
        "schedule": 60 * 60 * 24,   # every 24 hours
        "args": (30,),              # 30 days back
    },
}