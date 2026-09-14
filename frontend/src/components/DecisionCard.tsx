import { TiTick } from "react-icons/ti";
import { ImCross } from "react-icons/im";
import { Util } from "../util/Util";


export type DecisionSeverity = "Low" | "Medium" | "High"
interface Props{
    name: string
    change: string
    reason: string
    decisionSeverity?: DecisionSeverity
    date: Date
    approved?: boolean
    approver: string
}

export default function DecisionCard({name, change, reason, date, approved, decisionSeverity, approver} : Props) {
    
    return (
       <div className={`bg-panel2 border border-border   p-2 rounded-lg flex justify-between`}>
            <div className="flex flex-col gap-2 w-full">
                <div className="flex items-center gap-2 justify-between w-full">
                    <div className="flex items-center gap-2">
                        {approved === undefined ? "" :
                            <p className={`text-xs rounded-full
                                ${approved ? "border-low text-low" : "border-high text-high"}`}>
                                {approved ? <TiTick size={15}/> : <ImCross size={10}/>} 
                            </p>
                        }
                        <p className="text-subtext1 text-sm font-semibold">
                            {name}
                        </p>
                        {!decisionSeverity ? "" :
                            <p className="border border-border rounded-full text-subtext1 text-xs px-2 h-5 text-center bg-panel3">
                                {decisionSeverity}
                            </p>
                        }
                        <p className="border border-border rounded-full text-subtext1 text-xs px-2 h-5 text-center bg-panel3">
                            Approver: {approver}
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
            </div>
        </div>
    )
}
