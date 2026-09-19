import { useContext } from "react"
import Panel from "../primatives/Panel"
import PendingDecisionCard from "../PendingDecisionCard"
import { useWindowWidth } from "../hooks/useWindowWidth"
import IconTitle from "../primatives/IconTitle"
import { LuTimer } from "react-icons/lu";
import { FarmOverviewContext } from "../../providers/FarmOverviewProvider"
import { decisionName, decisionSeverity } from "../../util/ai-decisions"

export default function AwaitingDecisions() {
    const width = useWindowWidth()
    const overview = useContext(FarmOverviewContext)
    const pending = overview.decisions.filter(decision => decision.notification_status === "ready")

    return (
        <Panel styles="w-full p-3 px-4 flex flex-col gap-5">
            <IconTitle
                title="Awaiting Decisions"
                icon={<LuTimer />}
            />
            {overview.loading && pending.length === 0 ?
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
