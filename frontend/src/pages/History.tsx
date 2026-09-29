import { useContext, useEffect } from "react";
import { useLocation, useSearchParams } from "react-router";
import { RiFolderHistoryLine } from "react-icons/ri";
import AIDecisionsPanel from "../components/history-components/AIDecisionsPanel";
import CameraGalleryPanel from "../components/history-components/CameraGalleryPanel";
import SensorHistoryPanel from "../components/history-components/SensorHistoryPanel";
import SensorReadingsPanel from "../components/history-components/SensorReadingsPanel";
import PageTitlePanel from "../components/primatives/PageTitlePanel";
import { FarmOverviewContext } from "../providers/FarmOverviewProvider";

export default function History() {
    const overview = useContext(FarmOverviewContext)
    const farmKey = overview.farmId ?? "none"
    const [params] = useSearchParams()
    const sensor = params.get("sensor")
    const { hash } = useLocation()

    useEffect(() => {
        if (!hash) return
        document.getElementById(hash.slice(1))?.scrollIntoView({ block: "start" })
    }, [hash, farmKey])

    return (
        <div className="flex flex-col w-full items-center p-5 max-w-250 m-auto gap-5">
            <PageTitlePanel
                title="History"
                icon={ <RiFolderHistoryLine />}
            />
            <div id="sensor-history" className="w-full scroll-mt-20">
                <SensorHistoryPanel key={`${farmKey}-${sensor ?? "all"}`} />
            </div>
            <SensorReadingsPanel key={farmKey} />
            <div id="camera-gallery" className="w-full scroll-mt-20">
                <CameraGalleryPanel key={farmKey} />
            </div>
            <div id="ai-decisions" className="w-full scroll-mt-20">
                <AIDecisionsPanel key={farmKey} />
            </div>
        </div>
    )
}
