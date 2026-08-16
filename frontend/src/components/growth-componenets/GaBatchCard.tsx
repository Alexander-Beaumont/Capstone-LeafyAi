import type { GABatch } from "../../util/types"
import { Util } from "../../util/Util"
import XsButton from "../primatives/XsButton"

interface Props{
    batch: GABatch
}
export default function GaBatchCard({batch: b}: Props) {
    return (
        <div className={`border p-2 border-border rounded-md bg-panel3 flex-1 min-w-fit flex
                items-center justify-between`}>
                <div className="flex flex-col">                               
                    <p className="text-xs text-subtext1 font-semibold mb-1">
                        Batch: {b.batchId.slice(0, 4)}
                    </p>
                    <div className={`flex gap-3`}>
                        <p className="text-xs text-subtext2 ">
                        <span className="text-subtext3">Type</span> {b.plantType}
                        </p>
                        <p className="text-xs text-border ">
                            |
                        </p>
                        <p className="text-xs text-subtext2 ">
                            <span className="text-subtext3">Stage</span> {b.growthStage}
                        </p>
                        <p className="text-xs text-border ">
                            |
                        </p>
                        <p className="text-xs text-subtext2 ">
                            <span className="text-subtext3">Start Date </span> {Util.formatDate(b.GrowthAreaStartDate)}
                        </p> 
                        <p className="text-xs text-border ">
                            |
                        </p>
                        <p className="text-xs text-subtext2 ">
                            <span className="text-subtext3">End Date</span> {b.GrowthAreaEndDate ? Util.formatDate(b.GrowthAreaEndDate) : "N/A"}
                        </p>              
                    </div>
                </div>
                {!b.GrowthAreaEndDate ?
                    <XsButton
                        name="Edit"
                        onClick={() => {}}
                        highlight={false}
                    /> :
                    ""
                }
        </div>
    )
}
