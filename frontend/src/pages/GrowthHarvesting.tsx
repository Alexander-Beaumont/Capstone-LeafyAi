import InformationPanel from "../components/primatives/InformationPanel"
import PageTitlePanel from "../components/primatives/PageTitlePanel"
import { TbGrowth } from "react-icons/tb"
import Panel from "../components/primatives/Panel"
import IconTitle from "../components/primatives/IconTitle"
import { TiTick } from "react-icons/ti"
import BaBatchCard from "../components/growth-componenets/BaBatchCard"
import GaGrowingAreaCard from "../components/growth-componenets/GaGrowingAreaCard"
import XsButton from "../components/primatives/XsButton"
import { useContext, useState } from "react"
import Modal from "../components/primatives/Modal"
import GaEditCard from "../components/growth-componenets/GaEditCard"
import BaBatchEdit from "../components/growth-componenets/BaBatchEdit"
import { GrowthHarvestingContext } from "../providers/GrowthHarvestProvider"
import { Util } from "../util/Util"



export default function GrowthHarvesting() {
    const [openPanelId, setOpenPanelId] = useState("")
    const [editGrowingAreas, setEditGrowingAreas] = useState(false)
    const [editBatches, setEditBatches] = useState(false)

    const growthHarvesting = useContext(GrowthHarvestingContext)
   
    return (
        <div className="flex flex-col w-full items-center p-5 max-w-250 m-auto gap-5">
            <PageTitlePanel
                title="Growth & Harvesting"
                icon={<TbGrowth/>}
            />
            <div className="flex gap-3 w-full flex-wrap">
                <InformationPanel
                    name="Active Batches"
                    value={`${growthHarvesting.batches.filter(b => b.status == "active").length}`}
                />
                <InformationPanel
                    name="Completed Batches"
                    value={`${growthHarvesting.batches.filter(b => b.status == "completed").length}`}
                />
                <InformationPanel
                    name="Avg Batch Age"
                    value={`${Util.millisecondsToDays(Util.avgAge(growthHarvesting.batches.map(b => new Date(b.batchPlantDate))), 2)}d`}
                />
                <InformationPanel
                    name="Growing Area Usage"
                    value={`${growthHarvesting.growingAreas.filter(ga => ga.batches.filter(b => !b.GrowthAreaEndDate).length > 0).length / growthHarvesting.growingAreas.length * 100}%`}
                />
            </div>
            <Panel styles="w-full p-3 flex flex-col gap-3">
                <div className="flex items-center justify-between">
                    <IconTitle
                        title="Growing Areas"
                        icon={<TiTick size={15}/>}
                    />
                    <XsButton
                        name={"Edit"}
                        onClick={() => setEditGrowingAreas(!editGrowingAreas)}
                        highlight={false}
                    />
                </div>
                <div className="flex flex-col gap-3 max-h-108 h-108 overflow-y-scroll rounded-md no-scrollbar">
                    {growthHarvesting.growingAreas.map(ga => {
                        return <GaGrowingAreaCard 
                                    growingArea={ga} 
                                    openPanelId={openPanelId} 
                                    setOpenPanelId={setOpenPanelId}
                                    key={Math.random()}
                                />
                    })}  
                    {new Array(5 - growthHarvesting.growingAreas.length).fill(undefined).map(_ => {
                        return <div key={Math.random()} className="border border-dashed border-border min-h-19 rounded-md bg-panel2"></div>
                    })}
                </div>
            </Panel>
            <Panel styles="w-full p-3 flex flex-col gap-3 mb-20">
                <div className="flex items-center justify-between">
                    <IconTitle
                        title="Active Batches"
                        icon={<TiTick size={15}/>}
                    />
                    <XsButton
                        name={"Edit"}
                        onClick={() => setEditBatches(!editBatches)}
                        highlight={false}
                    />
                </div>
                <div className="flex flex-col gap-3 max-h-108 h-108 overflow-y-scroll rounded-md no-scrollbar">
                    {growthHarvesting.batches.filter(b => b.status != "Terminated").map(b => {
                        return <BaBatchCard key={Math.random()} batchInfo={b} openPanelId={openPanelId} setOpenPanelId={setOpenPanelId}/>
                    })}
                    {new Array(5 - growthHarvesting.batches.filter(b => b.status == "Active").length).fill(undefined).map(_ => {
                        return <div key={Math.random()} className="border border-dashed border-border min-h-19 rounded-md bg-panel2"></div>
                    })}
                </div>
            </Panel>
            <Modal open={editGrowingAreas} onClose={() => setEditGrowingAreas(false)}>
               <GaEditCard 
                    opened={editGrowingAreas} 
                    setOpend={(setEditGrowingAreas)}    
                />
            </Modal>
            <Modal open={editBatches} onClose={() => setEditBatches(false)}>
                <BaBatchEdit 
                    opened={editBatches} 
                    setOpend={(setEditBatches)} 
                />
            </Modal>
        </div>
    )
}
