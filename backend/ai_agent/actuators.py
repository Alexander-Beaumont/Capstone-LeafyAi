"""Audited AI actions through the shared current powerboard bridge."""
from django.utils import timezone

from ai_agent.models import FarmAction
from powerboard_control.bridge import get_powerboard_bridge

FAN_DEVICE_ID = 4
LIGHT_DEVICE_IDS = [5, 6]


def _current_states(bridge, device_ids):
    statuses = bridge.get_all_device_statuses()
    by_id = {row.get("device_id"): row for row in statuses}
    states = []
    for device_id in device_ids:
        row = by_id.get(device_id)
        state = str((row or {}).get("state", "")).upper()
        if state not in {"ON", "OFF"}:
            raise RuntimeError(f"Unable to read current state for powerboard device {device_id}.")
        states.append(state.lower())
    return states


def execute_decision(decision):
    if decision.execution_type != "automated" or decision.target_device not in {"fans", "light"}:
        return []

    ids = [FAN_DEVICE_ID] if decision.target_device == "fans" else list(LIGHT_DEVICE_IDS)
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
        previous_states = _current_states(bridge, ids)
        action.previous_state = (
            previous_states[0]
            if len(set(previous_states)) == 1
            else "mixed"
        )

        responses = []
        errors = []
        confirmed_ids = []
        for device_id in ids:
            try:
                response = bridge.set_device_state(device_id, requested)
                responses.append(response)
                confirmed = str(response.get("state", "unknown")).upper()
                if confirmed == requested:
                    confirmed_ids.append(device_id)
                else:
                    errors.append(
                        {
                            "device_id": device_id,
                            "error": f"confirmed {confirmed} after requesting {requested}",
                        }
                    )
            except Exception as exc:
                errors.append({"device_id": device_id, "error": str(exc)})

        action.hardware_response = {"devices": responses, "errors": errors}
        action.executed_at = timezone.now()

        if len(confirmed_ids) == len(ids):
            action.confirmed_state = requested.lower()
            action.result = "success"
            action.explanation = (
                "Hardware was already in the requested state."
                if action.previous_state == action.confirmed_state
                else "Powerboard confirmed the requested state."
            )
        elif confirmed_ids:
            action.confirmed_state = "mixed"
            action.result = "partial"
            action.explanation = (
                f"Powerboard confirmed {requested} for {len(confirmed_ids)} "
                f"of {len(ids)} target devices."
            )
        else:
            confirmed_states = {
                str(response.get("state", "unknown")).lower()
                for response in responses
            }
            action.confirmed_state = (
                confirmed_states.pop()
                if len(confirmed_states) == 1
                else "unknown"
            )
            action.result = "failed"
            action.explanation = (
                f"No target powerboard device confirmed {requested}."
            )
    except Exception as exc:
        action.result = "failed"
        action.explanation = str(exc)
        action.hardware_response = {"devices": [], "errors": [{"error": str(exc)}]}
    action.save()
    return [action]
