"""Direct, audited Kasa strip control for approved AI decisions."""

from asgiref.sync import async_to_sync
from django.utils import timezone

from ai_agent.models import FarmAction, KasaActuator


async def _set_kasa_socket(host, child_index, requested_state):
    from kasa.iot import IotStrip

    strip = IotStrip(host)
    await strip.update()
    if child_index >= len(strip.children):
        raise IndexError(f"Kasa child index {child_index} does not exist on {host}.")
    plug = strip.children[child_index]
    previous = "on" if plug.is_on else "off"
    if previous != requested_state:
        if requested_state == "on":
            await plug.turn_on()
        else:
            await plug.turn_off()
        await strip.update()
    confirmed = "on" if strip.children[child_index].is_on else "off"
    return previous, confirmed


def read_actuator(actuator):
    async def _read():
        from kasa.iot import IotStrip

        strip = IotStrip(actuator.host)
        await strip.update()
        if actuator.child_index >= len(strip.children):
            raise IndexError(f"Kasa child index {actuator.child_index} does not exist.")
        return "on" if strip.children[actuator.child_index].is_on else "off"

    return async_to_sync(_read)()


def execute_decision(decision):
    if decision.execution_type != "automated" or decision.target_device not in {"fans", "light"}:
        return []
    mappings = KasaActuator.objects.filter(
        farm=decision.run.farm,
        target_device=decision.target_device,
        enabled=True,
    )
    actions = []
    if not mappings.exists():
        return [
            FarmAction.objects.create(
                decision=decision,
                requested_state=decision.device_state,
                attempted_at=timezone.now(),
                result="failed",
                explanation=f"No enabled Kasa mapping exists for {decision.target_device}.",
            )
        ]
    for actuator in mappings:
        action = FarmAction.objects.create(
            decision=decision,
            actuator=actuator,
            requested_state=decision.device_state,
            attempted_at=timezone.now(),
        )
        try:
            previous, confirmed = async_to_sync(_set_kasa_socket)(
                actuator.host, actuator.child_index, decision.device_state
            )
            action.previous_state = previous
            action.confirmed_state = confirmed
            action.executed_at = timezone.now()
            if confirmed != decision.device_state:
                action.result = "failed"
                action.explanation = f"Kasa reported {confirmed} after requesting {decision.device_state}."
            else:
                action.result = "success"
                action.explanation = (
                    "Socket was already in the requested state."
                    if previous == confirmed
                    else "Kasa confirmed the requested state."
                )
        except Exception as exc:
            action.result = "failed"
            action.explanation = str(exc)
        action.save()
        actions.append(action)
    return actions
