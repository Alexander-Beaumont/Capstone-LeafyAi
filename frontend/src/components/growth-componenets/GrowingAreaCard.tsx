import { Util } from "../../util/Util";
import type { GrowingArea } from "./BatchCard";


interface Props{
    growingArea: GrowingArea
}
export default function GrowingAreaCard({growingArea: p}: Props) {
    return (
        <div className="border p-2 border-border rounded-md bg-panel3 flex-1 min-w-fit">
            <p className="text-xs text-subtext1 font-semibold mb-1">
                {p.growingAreaName}
            </p>
            <p className="text-xs text-subtext2 ">
                Slot Count: {p.slotCount}
            </p>
            <p className="text-xs text-subtext2 ">
                Farm Level: {p.farmLevel}
            </p>
            {p.endDate ? 
                <>
                    <p className="text-xs text-subtext2 ">
                        Start Date: {Util.formatDate(p.startDate)}
                    </p> 
                     <p className="text-xs text-subtext2 ">
                        End Date: {Util.formatDate(p.endDate)}
                    </p> 
                </>:
                <p className="text-xs text-subtext2 ">
                    Start Date: {Util.formatDate(p.startDate)}
                </p>
            }
        </div>
    )
}
