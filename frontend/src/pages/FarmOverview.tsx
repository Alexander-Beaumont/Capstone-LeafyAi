
import { useContext, useEffect, useState } from "react";
import { LuHouse } from "react-icons/lu";
import SensorReadings from "../components/overview-components/SensorReadings";
import DeviceControls from "../components/overview-components/DeviceControls";
import AwaitingDecisions from "../components/overview-components/AwaitingDecisions";
import PageTitlePanel from "../components/primatives/PageTitlePanel";
import { FarmOverviewContext } from "../providers/FarmOverviewProvider";
import InformationPanel from "../components/primatives/InformationPanel";
import { formatTimestamp, ingestionLabel } from "../util/operator";
import { PAGES } from "../util/constants";

export default function FarmOverview() {
    const overview = useContext(FarmOverviewContext)
    const [now, setNow] = useState(Date.now())

    useEffect(() => {
        const tick = setInterval(() => setNow(Date.now()), 1000)
        return () => clearInterval(tick)
    }, [])

    const dashboard = overview.dashboard
    const counts = dashboard?.sensors.counts
    const sensorValue = counts ? `${counts.fresh}/${counts.total}` : "…"
    const sensorHint = counts
        ? `${counts.stale} stale, ${counts.missing} missing, ${counts.suspect} suspect quality`
        : undefined
    const quality = dashboard?.cameras.image_quality

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
            {!overview.farmId ?
                <p className="w-full text-sm text-subtext3">Select a farm in the navigation bar.</p>
            :
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 w-full">
                    <InformationPanel
                        name="Ingestion"
                        value={ingestionLabel(dashboard?.sensors.ingestion_status)}
                        hint={dashboard ? `Last collection ${formatTimestamp(dashboard.sensors.last_successful_collection)}` : undefined}
                        muted={dashboard?.sensors.ingestion_status !== "healthy"}
                        loading={overview.loading && !dashboard}
                        to={`${PAGES.authPages.history}#sensor-history`}
                    />
                    <InformationPanel
                        name="Fresh sensors"
                        value={sensorValue}
                        hint={sensorHint}
                        loading={overview.loading && !dashboard}
                        to={`${PAGES.authPages.history}#sensor-history`}
                    />
                    <InformationPanel
                        name="Cameras"
                        value={dashboard ? String(dashboard.cameras.count) : "…"}
                        hint={dashboard ? `Next capture ${formatTimestamp(dashboard.cameras.next_capture)}` : undefined}
                        loading={overview.loading && !dashboard}
                        to={`${PAGES.authPages.history}#camera-gallery`}
                    />
                    <InformationPanel
                        name="Image quality"
                        value={quality?.status ?? "None"}
                        hint={quality?.message || (quality ? (quality.vlm_ready ? "VLM ready" : "Not VLM ready") : "No image")}
                        muted={!quality || quality.status === "FAIL" || quality.status === "UNKNOWN"}
                        loading={overview.loading && !dashboard}
                        to={`${PAGES.authPages.history}#camera-gallery`}
                    />
                    <InformationPanel
                        name="AI schedule"
                        value={dashboard?.ai.schedule_state === "enabled" ? "On" : dashboard ? "Off" : "…"}
                        hint={dashboard ? `Next window ${formatTimestamp(dashboard.ai.next_eligible_window)}` : undefined}
                        muted={dashboard?.ai.schedule_state !== "enabled"}
                        loading={overview.loading && !dashboard}
                        to={`${PAGES.authPages.history}#ai-decisions`}
                    />
                </div>
            }
            <div className="grid grid-cols-[minmax(0,auto)_minmax(0,1fr)] gap-5 w-full">
                <SensorReadings/>
               <DeviceControls/>
            </div>
           <AwaitingDecisions/>
        </div>
    )
}
