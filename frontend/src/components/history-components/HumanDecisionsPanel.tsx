import IconTitle from "../primatives/IconTitle"
import Panel from "../primatives/Panel"
import DecisionCard from "../DecisionCard"
import { LuUser } from "react-icons/lu"
import { placeHolderDecisions } from "../../util/constants"
import { type DecisionSeverity } from "../PendingDecisionCard"

export default function HumanDecisionsPanel() {
    return (
        <Panel styles="w-full p-3 flex flex-col gap-5">
            <IconTitle
                title="Human Decisions"
                icon={<LuUser />}
            />
            <div className="flex flex-col gap-3">
                {placeHolderDecisions.map(d => {
                    return(
                        <DecisionCard
                            name={d.name}
                            change={d.change}
                            reason={d.reason}
                            decisionSeverity={d.decisionSeverity as DecisionSeverity}
                            date={new Date()}
                            approver={d.approver}
                        />
                    )
                })}
            </div>
        </Panel>
    )
}
