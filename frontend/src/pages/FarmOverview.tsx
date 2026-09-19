
import { useContext, useEffect, useState } from "react";
import { LuHouse } from "react-icons/lu";
import SensorReadings from "../components/overview-components/SensorReadings";
import DeviceControls from "../components/overview-components/DeviceControls";
import AwaitingDecisions from "../components/overview-components/AwaitingDecisions";
import PageTitlePanel from "../components/primatives/PageTitlePanel";
import { FarmOverviewContext } from "../providers/FarmOverviewProvider";

export default function FarmOverview() {
    const overview = useContext(FarmOverviewContext)
    const [now, setNow] = useState(Date.now())

    useEffect(() => {
        const tick = setInterval(() => setNow(Date.now()), 1000)
        return () => clearInterval(tick)
    }, [])

    const secondsLeft = overview.nextRefreshAt == null
        ? 0
        : Math.max(0, Math.ceil((overview.nextRefreshAt - now) / 1000))
    const refreshLabel = overview.loading
        ? "Refreshing…"
        : overview.nextRefreshAt == null
            ? ""
            : `Next refresh in ${secondsLeft}s`

    return (
        <div className="flex flex-col w-full items-center p-5 max-w-250 m-auto gap-5">
            <PageTitlePanel
                title="Farm Overview"
                icon={ <LuHouse />}
                refresh={true}
                refreshing={overview.loading}
                refreshLabel={refreshLabel}
                onRefresh={() => overview.setUpdate(Math.random())}
            />
            <div className="grid grid-cols-[minmax(0,auto)_minmax(0,1fr)] gap-5 w-full">
                <SensorReadings/>
               <DeviceControls/>
            </div>
           <AwaitingDecisions/>
        </div>
    )
}
