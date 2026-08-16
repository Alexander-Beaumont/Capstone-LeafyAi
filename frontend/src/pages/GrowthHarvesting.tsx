import InformationPanel from "../components/primatives/InformationPanel"
import PageTitlePanel from "../components/primatives/PageTitlePanel"
import { TbGrowth } from "react-icons/tb"
import Panel from "../components/primatives/Panel"
import IconTitle from "../components/primatives/IconTitle"
import { TiTick } from "react-icons/ti"
import BaBatchCard from "../components/growth-componenets/BaBatchCard"
import { BaBatches, GaGrowingAreas } from "../util/constants"
import GaGrowingAreaCard from "../components/growth-componenets/GaGrowingAreaCard"
import XsButton from "../components/primatives/XsButton"
import { useState } from "react"
import Modal from "../components/primatives/Modal"
import GaEditCard from "../components/growth-componenets/GaEditCard"



export default function GrowthHarvesting() {
    const [openPanelId, setOpenPanelId] = useState("")
    const [editGrowingAreas, setEditGrowingAreas] = useState(false)

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
                    {GaGrowingAreas.map(ga => {
                        return <GaGrowingAreaCard growingArea={ga} openPanelId={openPanelId} setOpenPanelId={setOpenPanelId}/>
                    })}
                    {(openPanelId == "" || BaBatches.filter(b => b.status == "Active").map(b => b.batchId).includes(openPanelId)) &&
                        <>
                            {new Array(5 - GaGrowingAreas.length).fill(undefined).map(_ => {
                                return <div className="border border-dashed border-border h-19 rounded-md bg-panel2"></div>
                            })}
                        </>
                    }
                </div>
            </Panel>
            <Panel styles="w-full p-3 flex flex-col gap-3 mb-20">
                <IconTitle
                    title="Active Batches"
                    icon={<TiTick size={15}/>}
                />
                <div className="flex flex-col gap-3 max-h-108 h-108 overflow-y-scroll rounded-md no-scrollbar">
                    {BaBatches.filter(b => b.status == "Active").map(b => {
                        return <BaBatchCard batchInfo={b} openPanelId={openPanelId} setOpenPanelId={setOpenPanelId}/>
                    })}
                    {(openPanelId == "" || GaGrowingAreas.map(g => g.growingAreaName).includes(openPanelId)) &&
                        <>
                            {new Array(5 - BaBatches.filter(b => b.status == "Active").length).fill(undefined).map(_ => {
                                return <div className="border border-dashed border-border h-19 rounded-md bg-panel2"></div>
                            })}
                        </>
                    }
                </div>
            </Panel>
            <Modal open={editGrowingAreas} onClose={() => setEditGrowingAreas(false)}>
               <GaEditCard opened={editGrowingAreas} setOpend={(setEditGrowingAreas)}/>
            </Modal>
        </div>
    )
}
