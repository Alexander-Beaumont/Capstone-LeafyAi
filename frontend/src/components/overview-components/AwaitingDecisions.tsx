import Panel from "../primatives/Panel"
import PendingDecisionCard from "../PendingDecisionCard"
import { type DecisionSeverity } from "../PendingDecisionCard"
import { useWindowWidth } from "../hooks/useWindowWidth"
import { placeHolderDecisions } from "../../util/constants"
import IconTitle from "../primatives/IconTitle"
import { LuTimer } from "react-icons/lu";


export default function AwaitingDecisions() {
    const width = useWindowWidth()

    return (
        <Panel styles="w-full p-3 px-4 flex flex-col gap-5">
            <IconTitle
                title="Awaiting Decisions"
                icon={<LuTimer />}
            />
            <div className={`grid gap-3 ${width < 1000 ? "grid-cols-1" : "grid-cols-2"}`}>
                {placeHolderDecisions.map(d => {
                    return(
                        <PendingDecisionCard
                            name={d.name}
                            change={d.change}
                            reason={d.reason}
                            decisionSeverity={d.decisionSeverity as DecisionSeverity}
                            date={new Date()}
                            onAccept={() => {}}
                            onDecline={() => {}}
                        />
                    )
                })}
            </div>
        </Panel>
    )
}
