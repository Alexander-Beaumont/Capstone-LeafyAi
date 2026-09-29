import { useContext } from "react"
import PageTitlePanel from "../components/primatives/PageTitlePanel"
import Panel from "../components/primatives/Panel"
import IconTitle from "../components/primatives/IconTitle"
import AiAgentConfig from "../components/ai-agent/AiAgentConfig"
import CameraSettingsPanel from "../components/settings/CameraSettingsPanel"
import SensorIngestPanel from "../components/settings/SensorIngestPanel"
import CreateFarmForm from "../components/settings/CreateFarmForm"
import { GoGear } from "react-icons/go"
import { FarmOverviewContext } from "../providers/FarmOverviewProvider"

export default function Settings() {
    const overview = useContext(FarmOverviewContext)
    const farmKey = overview.farmId ?? "none"
    return (
        <div className="flex flex-col w-full items-center p-5 max-w-250 m-auto gap-5">
            <PageTitlePanel
                title="Settings"
                icon={ <GoGear />}
            />
            <Panel styles="w-full p-3 px-4 flex flex-col gap-4">
                <IconTitle title="New farm" icon={<GoGear />} />
                <CreateFarmForm />
            </Panel>
            <Panel styles="w-full p-3 px-4 flex flex-col gap-4">
                <IconTitle title="AI configuration" icon={<GoGear />} />
                <AiAgentConfig />
            </Panel>
            <SensorIngestPanel key={farmKey} />
            <CameraSettingsPanel key={farmKey} />
        </div>
    )
}
