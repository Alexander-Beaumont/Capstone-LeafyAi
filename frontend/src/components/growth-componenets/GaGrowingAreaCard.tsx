import { FaAngleLeft } from "react-icons/fa"
import { TiTick } from "react-icons/ti"
import { ImCross } from "react-icons/im"
import GaBatchCard from "./GaBatchCard"
import type { GAGrowingArea } from "../../util/types"
import { useMemo } from "react"

interface Props{
    growingArea: GAGrowingArea
    openPanelId: string
    setOpenPanelId: (id: string) => void
}

export default function GaGrowingAreaCard({growingArea: ga, openPanelId, setOpenPanelId} : Props) {
     
    const isOpen = useMemo(() => (ga.growingAreaName == openPanelId), [openPanelId])

    return (
        <div className="flex border-border bg-panel2 gap-2 border rounded-md p-3 flex-col">
            <div className="flex  items-center justify-between w-full">
                <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-1.5">
                        <div className={`text-xs p-1 rounded-full ${ga.batches.length <= 0 ? "bg-high" : "bg-btn"} `}>
                        </div>
                        <p className="text-xs text-subtext1">
                            Growing Area: {ga.growingAreaName}
                        </p>
                    </div>
                    <div className="flex gap-2 items-center">
                        
                        <p className="text-xs p-1 w-fit rounded-full px-3 bg-panel3 text-subtext2 border border-border">
                            Level: {ga.farmLevel}
                        </p>
                        <p className="text-xs p-1 w-fit rounded-full px-3 bg-panel3 text-subtext2 border border-border">
                            Slot Count: {ga.slotCount}
                        </p>
                    </div>
                </div>
                <div className={`hover:cursor-pointer  text-sm p-1 py-2 rounded-md text-subtext1 
                    duration-200 transition-all ${isOpen ? "-rotate-90" : "rotate-0"}`}
                    onClick={() => setOpenPanelId(isOpen ? "" : ga.growingAreaName)}>
                    <FaAngleLeft size={18}/>
                </div>
            </div>
            {isOpen && 
                <div className="flex flex-col gap-2">
                    <hr className="text-border"/>
                    <p className="text-xs text-subtext1 font-bold flex items-center">
                        <TiTick size={15} className="text-highlight"/> Current Batch
                    </p>
                    <div className="flex gap-3 flex-wrap">
                        {ga.batches.filter(b => !b.GrowthAreaEndDate).map(b => {
                            return  <GaBatchCard batch={b}/>
                        })}
                        {ga.batches.filter(b => !b.GrowthAreaEndDate).length == 0 &&
                            <p className="text-xs text-subtext3">
                                No batches currently in this growing area...
                            </p>
                        }
                    </div>
                    <p className="text-xs text-subtext1 font-bold flex items-center gap-1">
                        <ImCross size={8} className="text-high"/>  Previous batches
                    </p>
                    <div className="flex  gap-3 flex-wrap">
                        {ga.batches.filter(b => b.GrowthAreaEndDate != null).map(b => {
                            return  <GaBatchCard batch={b}/>
                        })}
                        {ga.batches.filter(b => b.GrowthAreaEndDate != null).length == 0 &&
                            <p className="text-xs text-subtext3">
                                No previous batches has used this growing area...
                            </p>
                        }
                    </div>
                </div>
            }
        </div>
    )
}
