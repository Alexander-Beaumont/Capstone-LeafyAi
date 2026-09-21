import { useContext } from "react"
import { Link } from "react-router"
import Panel from "../primatives/Panel"
import PendingDecisionCard from "../PendingDecisionCard"
import { useWindowWidth } from "../hooks/useWindowWidth"
import IconTitle from "../primatives/IconTitle"
import { LuTimer } from "react-icons/lu";
import { AiAgentContext } from "../../providers/AiAgentProvider"
import { decisionName, decisionSeverity } from "../../util/ai-decisions"
import { inputModeLabel } from "../../util/ai-agent"
import { PAGES } from "../../util/constants"

export default function AwaitingDecisions() {
    const width = useWindowWidth()
    const ai = useContext(AiAgentContext)
    const pending = (ai.latestRun?.recommendations ?? []).filter(decision => decision.notification_status === "ready")
    const lastRun = ai.latestRun

    return (
        <Panel styles="w-full p-3 px-4 flex flex-col gap-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
                <IconTitle
                    title="Awaiting Decisions"
                    icon={<LuTimer />}
                />
                {lastRun ?
                    <p className="text-xs text-subtext3">
                        Last run: {inputModeLabel(lastRun.input_mode, lastRun.fallback_used)}
                        {" · "}
                        <Link to={PAGES.authPages.aiAgent} className="text-highlight hover:underline">
                            AI Agent
                        </Link>
                    </p>
                : null}
            </div>
            {ai.loading && pending.length === 0 && !lastRun ?
                <p className="text-sm text-subtext3">
                    Loading…
                </p>
            : pending.length === 0 ?
                <p className="text-sm text-subtext3">
                    No decisions waiting
                </p>
            :
                <div className={`grid gap-3 ${width < 1000 ? "grid-cols-1" : "grid-cols-2"}`}>
                    {pending.map(decision => (
                        <PendingDecisionCard
                            key={decision.id}
                            name={decisionName(decision)}
                            change={decision.recommendation}
                            reason={decision.explanation}
                            decisionSeverity={decisionSeverity(decision.confidence_score)}
                            date={new Date(decision.created_at)}
                            onAccept={() => {}}
                            onDecline={() => {}}
                        />
                    ))}
                </div>
            }
        </Panel>
    )
}
