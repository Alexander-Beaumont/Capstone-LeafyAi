"""Audited AI actions through the shared current powerboard bridge."""
from django.utils import timezone

from ai_agent.models import FarmAction
from powerboard_control.bridge import get_powerboard_bridge

FAN_DEVICE_ID = 4
LIGHT_DEVICE_IDS = [5, 6]


def execute_decision(decision):
    if decision.execution_type != "automated" or decision.target_device not in {"fans", "light"}:
        return []

    ids = [FAN_DEVICE_ID] if decision.target_device == "fans" else LIGHT_DEVICE_IDS
    action = FarmAction.objects.create(
        decision=decision,
        target_device=decision.target_device,
        powerboard_device_ids=ids,
        requested_state=decision.device_state,
        attempted_at=timezone.now(),
    )
    requested = decision.device_state.upper()
    bridge = get_powerboard_bridge()
    try:
        with bridge.exclusive_operation():
            if decision.target_device == "fans":
                statuses = bridge.get_all_device_statuses()
                current = next(row for row in statuses if row.get("device_id") == FAN_DEVICE_ID)
                action.previous_state = str(current.get("state", "unknown")).lower()
                response = bridge.set_device_state(FAN_DEVICE_ID, requested)
                action.confirmed_state = str(response.get("state", "unknown")).lower()
            else:
                current = bridge.get_magenta_state()
                action.previous_state = str(current.get("state", "unknown")).lower()
                response = bridge.set_magenta_state(requested)
                action.confirmed_state = str(response.get("state", "unknown")).lower()
        action.hardware_response = response
        action.executed_at = timezone.now()
        if action.confirmed_state == decision.device_state:
            action.result = "success"
            action.explanation = "Hardware was already in the requested state." if action.previous_state == action.confirmed_state else "Powerboard confirmed the requested state."
        else:
            action.result = "failed"
            action.explanation = f"Powerboard confirmed {action.confirmed_state} after requesting {decision.device_state}."
    except Exception as exc:
        action.result = "failed"
        action.explanation = str(exc)
    action.save()
    return [action]
