import { inputModeLabel } from "../../util/ai-agent"
import type { RecommendationRun } from "../../util/types"
import Badge from "./Badge"
import CameraEvidence from "./CameraEvidence"
import RecommendationItem from "./RecommendationItem"

interface Props {
    run: RecommendationRun
    compact?: boolean
}

export default function RunDetails({ run, compact }: Props) {
    return (
        <div className={`flex flex-col ${compact ? "gap-3" : "gap-4"}`}>
            <div className="flex flex-wrap items-center gap-2">
                <Badge label={run.status} />
                <Badge label={inputModeLabel(run.input_mode, run.fallback_used)} />
                <Badge label={run.trigger} />
                <Badge label={`${run.provider_name}-${run.model_name}`} />

            </div>

            {run.fallback_used || run.fallback_reason ?
                <div className={`border border-border rounded-md bg-panel2 ${compact ? "p-2.5" : "p-3"}`}>
                    <p className={`${compact ? "text-xs" : "text-sm"} text-subtext1 font-semibold`}>Sensor-only fallback</p>
                    <p className="text-xs text-subtext3 mt-1">{run.fallback_reason || "The run used the LLM without vision input."}</p>
                </div>
            : null}
            {run.status === "failed" || run.error ?
                <div className={`border border-high rounded-md bg-panel2 ${compact ? "p-2" : "p-3"}`}>
                    <p className={`${compact ? "text-xs" : "text-sm"} text-high font-semibold`}>Run failed</p>
                    <p className="text-xs text-subtext2 mt-1">{run.error || "The model returned unusable output."}</p>
                </div>
            : null}
            {!compact ?
                <>
                    <CameraEvidence
                        evidence={run.visual_evidence ?? []}
                        sourceImages={run.source_images ?? []}
                        observations={run.image_observations ?? []}
                    />
                    <div className="flex flex-col gap-3">
                        {(run.recommendations ?? []).length === 0 ?
                            <p className="text-sm text-subtext3">No recommendations in this run.</p>
                        : run.recommendations.map(decision => (
                            <RecommendationItem key={decision.id} decision={decision} />
                        ))}
                    </div>
                </>
            : null}
        </div>
    )
}
