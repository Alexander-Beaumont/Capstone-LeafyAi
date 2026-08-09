import PageTitlePanel from "../components/primatives/PageTitlePanel"
import { TbGrowth } from "react-icons/tb"


export default function GrowthHarvesting() {
    return (
        <div className="flex flex-col w-full items-center p-5 max-w-250 m-auto gap-5">
            <PageTitlePanel
                title="AI Agent"
                icon={<TbGrowth/>}
            />
        </div>
    )
}
