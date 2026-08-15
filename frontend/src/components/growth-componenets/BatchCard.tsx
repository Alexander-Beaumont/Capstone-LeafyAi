import { useState } from "react"
import { FaAngleLeft } from "react-icons/fa"
import { TiTick } from "react-icons/ti"
import { ImCross } from "react-icons/im"
import GrowingAreaCard from "./GrowingAreaCard"
import { Util } from "../../util/Util"

export interface BatchInfo{
    plantType: string,
    batchPlantDate: Date,
    growthStage: string,
    status: string,
    batchId: string,
    growingAreas: GrowingArea[]
}
export interface GrowingArea{
    growingAreaName: string,
    slotCount: number,
    farmLevel: number,
    startDate: Date,
    endDate: Date | null
}
interface Props{
    batchInfo: BatchInfo
}


export default function BatchCard({batchInfo} : Props) {
    const [open, setOpen] = useState(false)

    return (
         <div className="flex border-border bg-panel2 gap-2 border rounded-md p-3 flex-col">
            <div className="flex  items-center justify-between w-full">
                <div className="flex flex-col gap-2">
                        <p className="text-xs text-subtext1">
                            Batch ID: {batchInfo.batchId}
                        </p>
                    <div className="flex gap-2 items-center">
                        
                        <p className="text-xs p-1 w-fit rounded-full px-3 bg-panel3 text-btn border border-btn">
                            {batchInfo.plantType}
                        </p>
                        <p className="text-xs p-1 w-fit rounded-full px-3 bg-panel3 text-btn border border-btn">
                            {Util.formatDate(batchInfo.batchPlantDate)}
                        </p>
                        <p className="text-xs p-1 w-fit rounded-full px-3 bg-panel3 text-btn border border-btn">
                            {batchInfo.growthStage}
                        </p>
                    </div>
                </div>
                <div className={`hover:cursor-pointer  text-sm p-1 py-2 rounded-md text-subtext1 
                    duration-200 transition-all ${open ? "-rotate-90" : "rotate-0"}`}
                    onClick={() => setOpen(!open)}>
                    <FaAngleLeft size={18}/>
                </div>
            </div>
            {open && 
                <div className="flex flex-col gap-2">
                    <hr className="text-border"/>
                    <p className="text-xs text-subtext1 font-bold flex items-center">
                        <TiTick size={15} className="text-highlight"/> Active Growing Areas 
                    </p>
                    <div className="flex gap-3 flex-wrap">
                        {batchInfo.growingAreas.filter(g => !g.endDate).map(g => {
                            return <GrowingAreaCard growingArea={g}/>
                        })}
                    </div>
                    <p className="text-xs text-subtext1 font-bold flex items-center gap-1">
                        <ImCross size={8} className="text-high"/>  Previous Growing Areas 
                    </p>
                    <div className="flex  gap-3 flex-wrap">
                         {batchInfo.growingAreas.filter(g => g.endDate).map(g => {
                            return <GrowingAreaCard growingArea={g}/>
                        })}
                    </div>
                </div>
            }
        </div>
    )
}
