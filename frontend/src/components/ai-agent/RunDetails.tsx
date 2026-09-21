import { Util } from "../../util/Util"
import { inputModeLabel } from "../../util/ai-agent"
import type { RecommendationRun } from "../../util/types"
import Badge from "./Badge"
import CameraEvidence from "./CameraEvidence"
import RecommendationItem from "./RecommendationItem"

interface Props {
    run: RecommendationRun
    compact?: boolean
}

function statusTone(status: RecommendationRun["status"]): "ok" | "warn" | "bad" | "default" {
    if (status === "completed") return "ok"
    if (status === "failed") return "bad"
    if (status === "running" || status === "pending") return "warn"
    return "default"
}

export default function RunDetails({ run, compact }: Props) {
    return (
        <div className="flex flex-col gap-4">
            <div className="flex flex-wrap items-center gap-2">
                <Badge label={run.status} tone={statusTone(run.status)} />
                <Badge label={inputModeLabel(run.input_mode, run.fallback_used)} tone={run.fallback_used || run.input_mode === "llm" ? "warn" : "ok"} />
                <Badge label={run.trigger} />
                <p className="text-xs text-subtext3">
                    {Util.formatDateTime(new Date(run.completed_at ?? run.created_at))}
                </p>
            </div>
            <p className="text-sm text-subtext2">
                {run.provider_name} / {run.model_name}
            </p>
            {run.fallback_used || run.fallback_reason ?
                <div className="border border-medium rounded-md bg-panel2 p-3">
                    <p className="text-sm text-medium font-semibold">Sensor-only fallback</p>
                    <p className="text-xs text-subtext2 mt-1">{run.fallback_reason || "The run used the LLM without vision input."}</p>
                </div>
            : null}
            {run.status === "failed" || run.error ?
                <div className="border border-high rounded-md bg-panel2 p-3">
                    <p className="text-sm text-high font-semibold">Run failed</p>
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
