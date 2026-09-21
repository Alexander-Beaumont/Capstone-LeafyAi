import PageTitlePanel from "../components/primatives/PageTitlePanel"
import Panel from "../components/primatives/Panel"
import IconTitle from "../components/primatives/IconTitle"
import AiAgentConfig from "../components/ai-agent/AiAgentConfig"
import { GoGear } from "react-icons/go"

export default function Settings() {
    return (
        <div className="flex flex-col w-full items-center p-5 max-w-250 m-auto gap-5">
            <PageTitlePanel
                title="Settings"
                icon={ <GoGear />}
            />
            <Panel styles="w-full p-3 px-4 flex flex-col gap-4">
                <IconTitle title="AI configuration" icon={<GoGear />} />
                <AiAgentConfig />
            </Panel>
        </div>
    )
}
