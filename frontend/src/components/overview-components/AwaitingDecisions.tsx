import Panel from "../primatives/Panel"
import DecisionCard from "../DecisionCard"
import { type DecisionSeverity } from "../DecisionCard"

export default function AwaitingDecisions() {
    const placeHolderDecisions = [{   
            name: "Run Pump",
            change: "AI agent has requested to run the pump at 2L/min for 45 seconds",
            reason: "Water level has decreased to 20%, ideal range is above 50%",
            decisionSeverity: "High",
        },{
            name: "Dim Lights",
            change: "AI agent has requested to dim the lights from 60% to 55%",
            reason: " To simulate natural cycles it is recommended to dim the ligths to 55%",
            decisionSeverity: "Low"
        },{
            name: "Run Doser",
            change: "AI agent has requested to run the doser for 10 seconds",
            reason: " pH level has been trending down",
            decisionSeverity: "Medium"
        }
    ]

    return (
        <Panel styles="w-full p-3 px-4 flex flex-col gap-5">
            <p className="text-md font-semibold text-title">
                Awaiting Decisions
            </p>
            {placeHolderDecisions.map(d => {
                return(
                    <DecisionCard
                        name={d.name}
                        change={d.change}
                        reason={d.reason}
                        decisionSeverity={d.decisionSeverity as DecisionSeverity}
                        onAccept={() => {}}
                        onDecline={() => {}}
                    />
                )
            })}
        </Panel>
    )
}
