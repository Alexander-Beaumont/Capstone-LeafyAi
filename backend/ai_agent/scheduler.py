from datetime import datetime, timedelta, timezone as datetime_timezone
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.utils import timezone

from ai_agent.models import AIConfiguration, AIRecommendationRun
from ai_agent.services import generate_recommendation


def schedule_slot(configuration, now=None):
    local_now = (now or timezone.now()).astimezone(ZoneInfo(configuration.timezone))
    start, end = configuration.active_start_time, configuration.active_end_time
    current = local_now.timetz().replace(tzinfo=None)
    if start < end:
        if not start <= current < end: return None
        start_date = local_now.date()
    else:
        if current >= start: start_date = local_now.date()
        elif current < end: start_date = local_now.date() - timedelta(days=1)
        else: return None
    window_start = datetime.combine(start_date, start, tzinfo=ZoneInfo(configuration.timezone))
    slot_index = max(0, int((local_now - window_start).total_seconds() // 60)) // configuration.interval_minutes
    return (window_start + timedelta(minutes=slot_index * configuration.interval_minutes)).astimezone(datetime_timezone.utc)


def run_due_schedules(now=None):
    for configuration in AIConfiguration.objects.filter(schedule_enabled=True).select_related("farm"):
        slot = schedule_slot(configuration, now)
        if slot is None: continue
        try:
            with transaction.atomic():
                run, created = AIRecommendationRun.objects.get_or_create(farm=configuration.farm, trigger="scheduled", scheduled_for=slot, defaults={"status": "pending"})
        except IntegrityError:
            continue
        if not created: continue
        try:
            generate_recommendation(configuration.farm, trigger="scheduled", scheduled_for=slot, run=run)
        except Exception as exc:
            # Generation normally persists its own failure. Cover failures that occur
            # before orchestration starts (for example, a farm without a device).
            run.refresh_from_db()
            if run.status not in {"completed", "failed"}:
                run.status = "failed"
                run.error = str(exc)
                run.completed_at = timezone.now()
                run.save(update_fields=["status", "error", "completed_at"])
            continue
