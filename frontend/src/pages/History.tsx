import { useContext } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router";
import { RiFolderHistoryLine } from "react-icons/ri";
import AIDecisionsPanel from "../components/history-components/AIDecisionsPanel";
import CameraGalleryPanel from "../components/history-components/CameraGalleryPanel";
import SensorHistoryPanel from "../components/history-components/SensorHistoryPanel";
import SensorReadingsPanel from "../components/history-components/SensorReadingsPanel";
import PageTitlePanel from "../components/primatives/PageTitlePanel";
import EmptyFarm from "../components/primatives/EmptyFarm";
import XsButton from "../components/primatives/XsButton";
import { FarmOverviewContext } from "../providers/FarmOverviewProvider";

const SECTIONS = [
    { id: "sensor-history", name: "Sensor history" },
    { id: "sensor-readings", name: "Readings" },
    { id: "camera-gallery", name: "Cameras" },
    { id: "ai-decisions", name: "AI decisions" },
] as const

type SectionId = (typeof SECTIONS)[number]["id"]

function sectionFromHash(hash: string): SectionId {
    const id = hash.replace("#", "")
    return SECTIONS.some(section => section.id === id) ? id as SectionId : "sensor-history"
}

export default function History() {
    const overview = useContext(FarmOverviewContext)
    const farmKey = overview.farmId ?? "none"
    const [params] = useSearchParams()
    const sensor = params.get("sensor")
    const location = useLocation()
    const navigate = useNavigate()
    const section = sectionFromHash(location.hash)

    function selectSection(id: SectionId) {
        navigate({ pathname: location.pathname, search: location.search, hash: id })
    }

    return (
        <div className="flex flex-col w-full items-center p-5 max-w-250 m-auto gap-5">
            <PageTitlePanel
                title="History"
                icon={ <RiFolderHistoryLine />}
            />
            {overview.loadError ? <p className="w-full text-sm text-high">{overview.loadError}</p> : null}
            {!overview.farmId ?
                <EmptyFarm noFarms={overview.farmsLoaded && overview.farms.length === 0 && !overview.loadError} />
            : <>
                <div className="flex w-full flex-wrap gap-2">
                    {SECTIONS.map(item => (
                        <XsButton
                            key={item.id}
                            name={item.name}
                            highlight={section === item.id}
                            onClick={() => selectSection(item.id)}
                        />
                    ))}
                </div>
                {section === "sensor-history" ?
                    <div className="w-full">
                        <SensorHistoryPanel key={`${farmKey}-${sensor ?? "all"}`} />
                    </div>
                : null}
                {section === "sensor-readings" ?
                    <div className="w-full">
                        <SensorReadingsPanel key={farmKey} />
                    </div>
                : null}
                {section === "camera-gallery" ?
                    <div className="w-full">
                        <CameraGalleryPanel key={farmKey} />
                    </div>
                : null}
                {section === "ai-decisions" ?
                    <div className="w-full">
                        <AIDecisionsPanel key={farmKey} />
                    </div>
                : null}
            </>}
        </div>
    )
}
