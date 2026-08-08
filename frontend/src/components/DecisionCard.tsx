import Button from "./primatives/Button"

export type DecisionSeverity = "Low" | "Medium" | "High"
interface Props{
    name: string
    change: string
    reason: string
    decisionSeverity: DecisionSeverity
    onAccept: () => void
    onDecline: () => void
}

export default function DecisionCard({name, change, reason, onAccept, onDecline, decisionSeverity} : Props) {
    
    const color = decisionSeverity == "Low" ? 
        "border-r-green-500" : 
        decisionSeverity == "Medium" ?
        "border-r-orange-500" :
        "border-r-red-500"

    return (
       <div className={`bg-panel2 border border-border border-r-8 ${color} p-2 rounded-lg flex justify-between`}>
            <div className="flex flex-col gap-2">
                <p className="text-subtext1 text-sm font-semibold">
                    {name}
                </p>
                <p className="text-sm text-subtext2">
                    {change}
                </p>
                <p className="text-sm text-subtext2">
                    <span className="font-bold italic">Reason: </span> 
                    {reason}
                </p>
                <div className="flex gap-3 w-full mt-2">
                    <Button
                        highlight={false}
                        name={"Decline"}
                        onSubmit={onDecline}
                    />
                    <Button
                        highlight={true}
                        name={"Accept"}
                        onSubmit={onAccept}
                    />
                </div>
            </div>
        </div>
    )
}
