import InformationPanel from "../components/primatives/InformationPanel"
import PageTitlePanel from "../components/primatives/PageTitlePanel"
import { TbGrowth } from "react-icons/tb"
import Panel from "../components/primatives/Panel"
import IconTitle from "../components/primatives/IconTitle"
import { TiTick } from "react-icons/ti"
import BatchCard from "../components/growth-componenets/BatchCard"
import { mockBatches } from "../util/constants"



export default function GrowthHarvesting() {

    return (
        <div className="flex flex-col w-full items-center p-5 max-w-250 m-auto gap-5">
            <PageTitlePanel
                title="Growth & Harvesting"
                icon={<TbGrowth/>}
            />
            <div className="flex gap-3 w-full flex-wrap">
                <InformationPanel
                    name="Active Batches"
                    value="3"
                />
                <InformationPanel
                    name="Completed Batches"
                    value="2"
                />
                <InformationPanel
                    name="Avg Batch Age"
                    value="24.5d"
                />
                <InformationPanel
                    name="Growing Area Usage"
                    value="88%"
                />
            </div>
            <Panel styles="w-full p-3 flex flex-col gap-3">
                <IconTitle
                    title="Active Batches"
                    icon={<TiTick size={15}/>}
                />
                <div className="flex flex-col gap-3 max-h-130 overflow-y-scroll rounded-md no-scrollbar">
                    {mockBatches.filter(b => b.status == "Active").map(b => {
                        return <BatchCard batchInfo={b}/>
                    })}
                </div>
            </Panel>
            <Panel styles="w-full p-3 flex flex-col gap-3">
                <IconTitle
                    title="Completed Batches"
                    icon={<TiTick size={15}/>}
                />
                <div className="flex flex-col gap-3 max-h-130 overflow-y-scroll rounded-md no-scrollbar">
                    {mockBatches.filter(b => b.status != "Active").map(b => {
                        return <BatchCard batchInfo={b}/>
                    })}
                </div>
            </Panel>
        </div>
    )
}
