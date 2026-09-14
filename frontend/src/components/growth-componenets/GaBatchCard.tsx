import { useState } from "react"
import type { GABatch, GAGrowingArea} from "../../util/types"
import { Util } from "../../util/Util"
import XsButton from "../primatives/XsButton"
import Modal from "../primatives/Modal"
import GaBatchEdit from "./GaBatchEdit"

interface Props{
    batch: GABatch
    currentGa: GAGrowingArea
}
export default function GaBatchCard({batch: b, currentGa}: Props) {
    const [editBatch, setEditBatch] = useState(false)

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
                            <span className="text-subtext3">Start Date </span> {Util.formatDate(new Date(b.GrowthAreaStartDate))}
                        </p> 
                        <p className="text-xs text-border ">
                            |
                        </p>
                        <p className="text-xs text-subtext2 ">
                            <span className="text-subtext3">End Date</span> {b.GrowthAreaEndDate ? Util.formatDate(new Date(b.GrowthAreaEndDate)) : "N/A"}
                        </p>              
                    </div>
                </div>
                {!b.GrowthAreaEndDate ?
                    <XsButton
                        name="Edit"
                        onClick={() => {setEditBatch(true)}}
                        highlight={false}
                    /> :
                    ""
                }
                <Modal onClose={() => setEditBatch(false)} open={editBatch}>
                    <GaBatchEdit opened={editBatch} setOpend={setEditBatch} currentGrowingArea={currentGa} currentBatch={b}/>
                </Modal>
        </div>
    )
}
