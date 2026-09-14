import type { BAGrowingArea } from "../../util/types";
import { Util } from "../../util/Util";

interface Props{
    growingArea: BAGrowingArea
}
export default function BaGrowingAreaCard({growingArea: p}: Props) {
    return (
        <div className={`border p-2 border-border rounded-md bg-panel3 flex-1 min-w-fit`}>
            <p className="text-xs text-subtext1 font-semibold mb-1">
                {p.growingAreaName}
            </p>
            <div className={`flex gap-3`}>
                <p className="text-xs text-subtext2 ">
                   <span className="text-subtext3">Slot Count</span> {p.slotCount}
                </p>
                <p className="text-xs text-border ">
                    |
                </p>
                <p className="text-xs text-subtext2 ">
                    <span className="text-subtext3">Farm Level</span> {p.farmLevel}
                </p>
                <p className="text-xs text-border ">
                    |
                </p>
                <p className="text-xs text-subtext2 ">
                    <span className="text-subtext3">Start Date </span> {Util.formatDate(new Date(p.startDate))}
                </p> 
                <p className="text-xs text-border ">
                    |
                </p>
                <p className="text-xs text-subtext2 ">
                    <span className="text-subtext3">End Date </span> {p.endDate ? Util.formatDate(new Date(p.endDate)) : "N/A"}
                </p>              
            </div>
        </div>
    )
}
