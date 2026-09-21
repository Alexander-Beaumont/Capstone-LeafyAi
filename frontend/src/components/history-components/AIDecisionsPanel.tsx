import { useContext, useState } from "react"
import Panel from "../primatives/Panel"
import IconTitle from "../primatives/IconTitle"
import { VscRobot } from "react-icons/vsc"
import { AiAgentContext } from "../../providers/AiAgentProvider"
import RunDetails from "../ai-agent/RunDetails"
import { inputModeLabel } from "../../util/ai-agent"

export default function AIDecisionsPanel() {
    const ai = useContext(AiAgentContext)
    const [openRunId, setOpenRunId] = useState<number | null>(null)

    return (
        <Panel styles="w-full p-3 flex flex-col gap-5">
            <IconTitle
                title="AI Decisions"
                icon={<VscRobot size={16}/>}
            />
            {ai.loading && ai.recentRuns.length === 0 ?
                <div className="h-24 bg-panel2 animate-pulse rounded-md" />
            : ai.recentRuns.length === 0 ?
                <p className="text-sm text-subtext3">No recommendation runs yet.</p>
            :
                <div className="flex flex-col gap-3">
                    {ai.recentRuns.map(run => {
                        const open = openRunId === run.id
                        return (
                            <div key={run.id} className="border border-border rounded-lg bg-panel2 p-3 flex flex-col gap-3">
                                <button
                                    type="button"
                                    className="flex flex-wrap items-center justify-between gap-2 text-left hover:cursor-pointer"
                                    onClick={() => setOpenRunId(open ? null : run.id)}
                                    aria-expanded={open}
                                >
                                    <span className="text-sm text-subtext1 font-semibold">
                                        Run {run.id} · {run.status} · {inputModeLabel(run.input_mode, run.fallback_used)}
                                    </span>
                                    <span className="text-xs text-subtext3">{open ? "Hide" : "Details"}</span>
                                </button>
                                {open ? <RunDetails run={run} /> : <RunDetails run={run} compact />}
                            </div>
                        )
                    })}
                </div>
            }
        </Panel>
    )
}
