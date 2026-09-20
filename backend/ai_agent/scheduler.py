"""In-web-process recommendation scheduler with database slot claims."""

import logging
import os
import threading
from datetime import datetime, timedelta, timezone as datetime_timezone
from time import sleep
from zoneinfo import ZoneInfo

from django.db import IntegrityError, close_old_connections, transaction
from django.utils import timezone

from ai_agent.models import AIConfiguration, AIRecommendationRun
from ai_agent.services import generate_recommendation

logger = logging.getLogger(__name__)
_started = False
_lock = threading.Lock()


def schedule_slot(configuration, now=None):
    now = now or timezone.now()
    local_now = now.astimezone(ZoneInfo(configuration.timezone))
    start, end = configuration.active_start_time, configuration.active_end_time
    local_time = local_now.timetz().replace(tzinfo=None)
    if start == end:
        window_start_date = local_now.date()
    elif start < end:
        if not (start <= local_time < end):
            return None
        window_start_date = local_now.date()
    else:
        if local_time >= start:
            window_start_date = local_now.date()
        elif local_time < end:
            window_start_date = local_now.date() - timedelta(days=1)
        else:
            return None
    window_start = datetime.combine(window_start_date, start, tzinfo=ZoneInfo(configuration.timezone))
    elapsed_minutes = max(0, int((local_now - window_start).total_seconds() // 60))
    slot_index = elapsed_minutes // configuration.interval_minutes
    return (window_start + timedelta(minutes=slot_index * configuration.interval_minutes)).astimezone(datetime_timezone.utc)


def run_due_schedules(now=None):
    for configuration in AIConfiguration.objects.filter(schedule_enabled=True).select_related("farm"):
        slot = schedule_slot(configuration, now=now)
        if slot is None:
            continue
        try:
            with transaction.atomic():
                run, created = AIRecommendationRun.objects.get_or_create(
                    farm=configuration.farm,
                    trigger="scheduled",
                    scheduled_for=slot,
                    defaults={"status": "pending"},
                )
        except IntegrityError:
            continue
        if not created:
            continue
        try:
            generate_recommendation(
                configuration.farm,
                trigger="scheduled",
                scheduled_for=slot,
                run=run,
            )
        except Exception:
            logger.exception("Scheduled AI recommendation failed for farm %s", configuration.farm_id)


def _loop():
    poll_seconds = max(5, int(os.environ.get("AI_WEB_SCHEDULER_POLL_SECONDS", "30")))
    while True:
        close_old_connections()
        try:
            run_due_schedules()
        except Exception:
            logger.exception("AI scheduler poll failed")
        finally:
            close_old_connections()
        sleep(poll_seconds)


def start_scheduler():
    global _started
    with _lock:
        if _started:
            return
        _started = True
        threading.Thread(target=_loop, name="leafyai-ai-scheduler", daemon=True).start()
