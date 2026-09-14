import Panel from "../primatives/Panel"
import Button from "../primatives/Button"
import Dropdown from "../primatives/Dropdown"
import { type dataFormat } from "../primatives/Dropdown"
import IconTitle from "../primatives/IconTitle"
import { useContext, useState } from "react"
import { TbEdit } from "react-icons/tb"
import type { GABatch, GAGrowingArea } from "../../util/types"
import { GrowthHarvestingContext } from "../../providers/GrowthHarvestProvider"
import { userContext } from "../../providers/UserProvider"
import { moveBatch } from "../../util/api-service-layer"

interface Props{
    opened: boolean
    setOpend: (state: boolean) => void
    currentGrowingArea: GAGrowingArea
    currentBatch: GABatch
}

export default function GaBatchEdit({setOpend, currentGrowingArea, currentBatch} : Props) {
    const gh = useContext(GrowthHarvestingContext)
    const user = useContext(userContext)

    const [selectedItem, setSelectedItem] = useState<dataFormat|null>(null)
    const items: dataFormat[] = gh.growingAreas
        .filter(g => g.growingAreaId != currentGrowingArea.growingAreaId)
        .map((g, i) => ({name: g.growingAreaName, id: i, data: g}))

    async function moveBatchToGa(){
        if(!selectedItem){
            alert("Select a growing area to move the batch to")
            return
        }

        user.setLoading(true)

        const res = await moveBatch(user.accessToken, {
            currentGaID: currentGrowingArea.growingAreaId,
            destinationGaID: (selectedItem.data as GAGrowingArea).growingAreaId,
            batchID: currentBatch.batchId
        })

        if(!res.success) {
            alert(res.data?.msg); 
        }else{
            setOpend(false)
            gh.setUpdate(Math.random())
        }
        user.setLoading(false)
    }

    return (
        <div onClick={e => e.stopPropagation()} className="w-[80%] max-w-120">
            <Panel styles="p-3  flex flex-col gap-3">
                <IconTitle
                        title="Move Batch"
                        icon={<TbEdit />}
                />
                <hr className="text-border"/>
                <div className="flex gap-2 items-center justify-between">
                        <p className="text-xs text-subtext1">
                            Select Growing Area To Move Batch To:
                        </p>
                        <Dropdown
                            items={items}
                            setSelectedItem={id => setSelectedItem(items.find(i => i.id == id)!)}
                            selectedItem={selectedItem}
                            defaultText="Select"
                        />
                </div>
                <hr className="text-border"/>
                <div className="flex gap-3 mt-3">
                    <Button
                        name="Close"
                        highlight={false}
                        onSubmit={() => {
                            setOpend(false)
                            setSelectedItem(null)
                        }}
                        styles={{ noAnimation: true}}
                    />
                    <Button
                        name="Update"
                        highlight={true}
                        onSubmit={() => moveBatchToGa()}
                        loading={user.loading}
                        styles={{ noAnimation: true}}
                    />
                </div>
            </Panel>
        </div>
    )
}
