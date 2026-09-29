import { useContext } from "react";
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

    return (
        <div className="flex flex-col w-full items-center p-5 max-w-250 m-auto gap-5">
            <PageTitlePanel
                title="History"
                icon={ <RiFolderHistoryLine />}
            />
            <SensorHistoryPanel key={farmKey} />
            <SensorReadingsPanel key={farmKey} />
            <CameraGalleryPanel key={farmKey} />
            <AIDecisionsPanel key={farmKey} />
        </div>
    )
}
