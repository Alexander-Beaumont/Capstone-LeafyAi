import { Util } from "../util/Util"

export type DecisionSeverity = "Low" | "Medium" | "High"
interface Props{
    name: string
    change: string
    reason: string
    decisionSeverity: DecisionSeverity
    date: Date
    onAccept: () => void
    onDecline: () => void
}

export default function PendingDecisionCard({name, change, reason, onAccept, onDecline, date, decisionSeverity} : Props) {

    return (
       <div className={`bg-panel2 border border-border  p-2 rounded-lg flex justify-between`}>
            <div className="flex flex-col gap-2 w-full">
                <div className="flex items-center gap-2 justify-between w-full">
                    <div className="flex items-center gap-2">
                        <p className="text-subtext1 text-sm font-semibold">
                            {name}
                        </p>
                        <p className="border border-border rounded-full text-subtext1 text-xs px-2 h-5 text-center bg-panel3">
                            {decisionSeverity}
                        </p>
                    </div>
                    <p className="rounded-full text-subtext3 px-2 text-xs h-5 text-center ">
                        {Util.formatDateTime(date)}
                    </p>
                </div>
                <p className="text-xs text-subtext2">
                    {change}
                </p>
                <p className="text-xs text-subtext2">
                    <span className="font-bold italic">Reason: </span> 
                    {reason}
                </p>
                <div className="flex gap-3 w-full  mt-2">
                    <button
                        className="border rounded-md  text-subtext3 text-xs px-2 p-1 text-center bg-panel3 opacity-60 cursor-not-allowed"
                        title="Approval is not available yet"
                        disabled
                    >
                        Decline
                    </button>
                    <button
                        className="border rounded-md text-highlight text-xs px-2 p-1 text-center bg-panel3 opacity-60 cursor-not-allowed"
                        title="Approval is not available yet"
                        disabled
                    >
                        Accept
                    </button>
                </div>
            </div>
        </div>
    )
}
