import PageTitlePanel from "../components/primatives/PageTitlePanel"
import { VscRobot } from "react-icons/vsc"

export default function AiAgent() {
    return (
        <div className="flex flex-col w-full items-center p-5 max-w-250 m-auto gap-5">
            <PageTitlePanel
                title="AI Agent"
                icon={<VscRobot/>}
            />
        </div>
    )
}
