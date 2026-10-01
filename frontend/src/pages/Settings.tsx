import { useContext, useState } from "react"
import { useLocation, useNavigate } from "react-router"
import PageTitlePanel from "../components/primatives/PageTitlePanel"
import Panel from "../components/primatives/Panel"
import IconTitle from "../components/primatives/IconTitle"
import Button from "../components/primatives/Button"
import XsButton from "../components/primatives/XsButton"
import Modal from "../components/primatives/Modal"
import AiAgentConfig from "../components/ai-agent/AiAgentConfig"
import CameraSettingsPanel from "../components/settings/CameraSettingsPanel"
import SensorIngestPanel from "../components/settings/SensorIngestPanel"
import CreateFarmForm from "../components/settings/CreateFarmForm"
import EmptyFarm from "../components/primatives/EmptyFarm"
import { GoGear } from "react-icons/go"
import { FarmOverviewContext } from "../providers/FarmOverviewProvider"
import { userContext } from "../providers/UserProvider"
import { deleteFarm } from "../util/api-service-layer"

const SECTIONS = [
    { id: "new-farm", name: "New farm" },
    { id: "ai-configuration", name: "AI configuration" },
    { id: "sensor-ingestion", name: "Sensor ingestion" },
    { id: "cameras", name: "Cameras" },
] as const

type SectionId = (typeof SECTIONS)[number]["id"]

function sectionFromHash(hash: string): SectionId {
    const id = hash.replace("#", "")
    return SECTIONS.some(section => section.id === id) ? id as SectionId : "new-farm"
}

export default function Settings() {
    const overview = useContext(FarmOverviewContext)
    const user = useContext(userContext)
    const farmKey = overview.farmId ?? "none"
    const location = useLocation()
    const navigate = useNavigate()
    const section = sectionFromHash(location.hash)
    const [confirmDelete, setConfirmDelete] = useState(false)
    const [deleting, setDeleting] = useState(false)
    const [deleteError, setDeleteError] = useState("")

    function selectSection(id: SectionId) {
        navigate({ pathname: location.pathname, search: location.search, hash: id })
    }

    async function removeFarm() {
        if (!user.accessToken || overview.farmId == null) return
        setDeleting(true)
        setDeleteError("")
        const result = await deleteFarm(user.accessToken, overview.farmId)
        setDeleting(false)
        if (!result.success) {
            setDeleteError(result.msg || "Could not delete the farm")
            return
        }
        setConfirmDelete(false)
        overview.setUpdate(Math.random())
    }

    return (
        <div className="flex flex-col w-full items-center p-5 max-w-250 m-auto gap-5">
            <PageTitlePanel
                title="Settings"
                icon={ <GoGear />}
            />
            {overview.loadError ? <p className="w-full text-sm text-high">{overview.loadError}</p> : null}
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
            {section === "new-farm" ? <>
                {overview.farmsLoaded && overview.farms.length === 0 && !overview.loadError ?
                    <EmptyFarm noFarms onSettings />
                : null}
                <Panel styles="w-full p-3 px-4 flex flex-col gap-4">
                    <IconTitle title="New farm" icon={<GoGear />} />
                    <CreateFarmForm />
                    {overview.farmId != null ?
                        <div className="flex flex-col gap-2 border-t border-border pt-4">
                            <p className="text-sm text-subtext1">Selected farm: {overview.farmName}</p>
                            <Button name="Delete farm" highlight={false} onSubmit={() => { setDeleteError(""); setConfirmDelete(true) }} />
                        </div>
                    : null}
                </Panel>
                <Modal open={confirmDelete} onClose={() => { if (!deleting) setConfirmDelete(false) }}>
                    <div
                        className="bg-panel1 border border-border p-5 flex flex-col rounded-xl w-[80%] max-w-xl gap-3"
                        onClick={event => event.stopPropagation()}
                    >
                        <p className="text-xl font-semibold text-title">Delete {overview.farmName}?</p>
                        <p className="text-sm text-subtext1">
                            This removes the controller, levels, growing areas, cameras, and sensor history for this farm.
                        </p>
                        {deleteError ? <p className="text-xs text-red-400">{deleteError}</p> : null}
                        <div className="flex gap-3">
                            <Button name="Delete farm" highlight loading={deleting} onSubmit={removeFarm} styles={{ noAnimation: true }} />
                            <Button name="Cancel" highlight={false} onSubmit={() => setConfirmDelete(false)} styles={{ noAnimation: true }} />
                        </div>
                    </div>
                </Modal>
            </> : null}
            {section === "ai-configuration" ?
                <Panel styles="w-full p-3 px-4 flex flex-col gap-4">
                    <IconTitle title="AI configuration" icon={<GoGear />} />
                    <AiAgentConfig />
                </Panel>
            : null}
            {section === "sensor-ingestion" ? <SensorIngestPanel key={`ingest-${farmKey}`} /> : null}
            {section === "cameras" ? <CameraSettingsPanel key={`cameras-${farmKey}`} /> : null}
        </div>
    )
}
