import { useMemo} from "react"
import { FaAngleLeft } from "react-icons/fa"
import { TiTick } from "react-icons/ti"
import { ImCross } from "react-icons/im"
import BaGrowingAreaCard from "./BaGrowingAreaCard"
import { Util } from "../../util/Util"
import type { BABatch } from "../../util/types"

interface Props{
    batchInfo: BABatch
    openPanelId: string
    setOpenPanelId: (id: string) => void
}

export default function BaBatchCard({batchInfo, openPanelId, setOpenPanelId} : Props) {

    const isOpen = useMemo(() => (batchInfo.batchId == openPanelId), [openPanelId])

    return (
        <div className="flex border-border bg-panel2 gap-2 border rounded-md p-3 flex-col">
            <div className="flex  items-center justify-between w-full">
                <div className="flex flex-col gap-2">
                        <p className="text-xs text-subtext1">
                            Batch ID: {batchInfo.batchId}
                        </p>
                    <div className="flex gap-2 items-center">
                        <p className="text-xs p-1 w-fit rounded-full px-3 bg-panel3 text-subtext2 border border-border">
                            {batchInfo.plantType}
                        </p>
                        <p className="text-xs p-1 w-fit rounded-full px-3 bg-panel3 text-subtext2 border border-border">
                            {Util.formatDate(new Date(batchInfo.batchPlantDate))}
                        </p>
                        <p className="text-xs p-1 w-fit rounded-full px-3 bg-panel3 text-subtext2 border border-border">
                            {batchInfo.growthStage}
                        </p>
                        <p className="text-xs p-1 w-fit rounded-full px-3 bg-panel3 text-subtext2 border border-border">
                            {batchInfo.status}
                        </p>
                    </div>
                </div>
                <div className={`hover:cursor-pointer  text-sm p-1 py-2 rounded-md text-subtext1 
                    duration-200 transition-all ${isOpen ? "-rotate-90" : "rotate-0"}`}
                    onClick={() => setOpenPanelId(isOpen ? "" : batchInfo.batchId)}>
                    <FaAngleLeft size={18}/>
                </div>
            </div>
            {isOpen && 
                <div className="flex flex-col gap-2">
                    <hr className="text-border"/>
                    <p className="text-xs text-subtext1 font-bold flex items-center">
                        <TiTick size={15} className="text-highlight"/> Current Growing Area
                    </p>
                    <div className="flex gap-3 flex-wrap">
                        {batchInfo.growingAreas.filter(g => !g.endDate).map(g => {
                            return <BaGrowingAreaCard growingArea={g}/>
                        })}
                        {batchInfo.growingAreas.filter(g => !g.endDate).length == 0 &&
                            <p className="text-xs text-subtext3">
                                Batch is not currently in a growing area
                            </p>
                        }
                    </div>
                    <p className="text-xs text-subtext1 font-bold flex items-center gap-1">
                        <ImCross size={8} className="text-high"/>  Previous Growing Areas 
                    </p>
                    <div className="flex  gap-3 flex-wrap">
                        {batchInfo.growingAreas.filter(g => g.endDate).map(g => {
                            return <BaGrowingAreaCard growingArea={g}/>
                        })}
                        {batchInfo.growingAreas.filter(g => g.endDate).length == 0 &&
                            <p className="text-xs text-subtext3">
                                Batch does not have any previous growing areas
                            </p>
                        }
                    </div>
                </div>
            }
        </div>
    )
}
