import Panel from "../primatives/Panel"
import IconTitle from "../primatives/IconTitle"
import { VscRobot } from "react-icons/vsc"
import { placeHolderDecisions } from "../../util/constants"
import DecisionCard from "../DecisionCard"
import { type DecisionSeverity } from "../PendingDecisionCard"

export default function AIDecisionsPanel() {
    return (
        <Panel styles="w-full p-3 flex flex-col gap-5">
            <IconTitle
                title="AI Decisions"
                icon={<VscRobot size={16}/>}
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
                            approved={d.approved}
                            approver={d.approver}
                        />
                    )
                })}
            </div>
        </Panel>
    )
}
