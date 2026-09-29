import { recommendationBadges } from "../../util/ai-agent"
import { decisionName, decisionSeverity } from "../../util/ai-decisions"
import type { AIDecision, FarmAction } from "../../util/types"
import Badge from "./Badge"

interface Props {
    decision: AIDecision
}

export default function RecommendationItem({ decision }: Props) {
    const badges = recommendationBadges(decision)
    const safety = decision.safety_check

    return (
        <div className="border border-border rounded-lg bg-panel2 p-3 flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm text-subtext1 font-semibold">{decisionName(decision)}</p>
                <Badge label={decisionSeverity(decision.confidence_score)} />
                {badges.map(badge => (
                    <Badge key={`${decision.id}-${badge}`} label={badge} />
                ))}
            </div>
            <p className="text-xs text-subtext2">{decision.recommendation}</p>
            <p className="text-xs text-subtext2">
                <span className="font-bold italic">Reason: </span>
                {decision.explanation}
            </p>
            {safety ?
                <p className="text-xs text-subtext3">
                    Safety {safety.result}: {safety.explanation || "No explanation."}
                </p>
            : null}
            {(decision.actions ?? []).map(action => (
                <div key={action.id} className="flex flex-col gap-1">
                    <p className="text-xs text-subtext3">
                        {action.target_device} {action.requested_state}
                        {action.powerboard_device_ids.length ? ` [${action.powerboard_device_ids.join(", ")}]` : ""}
                        {action.result ? ` — ${action.result}` : ""}
                        {action.explanation ? `. ${action.explanation}` : ""}
                    </p>
                    {action.result === "partial" ? <HardwareResult action={action} /> : null}
                </div>
            ))}
        </div>
    )
}

function HardwareResult({ action }: { action: FarmAction }) {
    const devices = Array.isArray(action.hardware_response.devices)
        ? action.hardware_response.devices as { device_id?: number, name?: string, state?: string }[]
        : []
    const errors = Array.isArray(action.hardware_response.errors)
        ? action.hardware_response.errors as { device_id?: number, error?: string }[]
        : []
    if (devices.length === 0 && errors.length === 0) return null
    return (
        <ul className="text-xs text-subtext3 list-disc pl-4">
            {devices.map(device => (
                <li key={`ok-${device.device_id}`}>
                    Outlet {device.name ?? device.device_id} succeeded{device.state ? ` (${device.state})` : ""}.
                </li>
            ))}
            {errors.map((failure, index) => (
                <li key={`fail-${failure.device_id ?? index}`}>
                    Outlet {failure.device_id ?? "unknown"} failed{failure.error ? `: ${failure.error}` : ""}.
                </li>
            ))}
        </ul>
    )
}
