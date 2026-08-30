import Panel from "../primatives/Panel"
import Button from "../primatives/Button"
import Dropdown from "../primatives/Dropdown"
import { type dataFormat } from "../primatives/Dropdown"
import IconTitle from "../primatives/IconTitle"
import { useContext, useState } from "react"
import XsButton from "../primatives/XsButton"
import { TbEdit } from "react-icons/tb"
import type { BABatch, GAGrowingArea } from "../../util/types"
import TextBox from "../primatives/Textbox"
import useForm from "../hooks/useFrom"
import { userContext } from "../../providers/UserProvider"
import type { APIResult } from "../../util/types"
import { createBatch, updateBatch } from "../../util/api-service-layer"
import { GrowthHarvestingContext } from "../../providers/GrowthHarvestProvider"

interface Props{
    opened: boolean
    setOpend: (state: boolean) => void
}

export default function BaBatchEdit({setOpend} : Props) {
    const user = useContext(userContext)
    const gh = useContext(GrowthHarvestingContext)

    const [edit, setEdit] = useState(false)
    const [selectedBatchItem, setSelectedBatchItem] = useState<dataFormat|null>(null)

    const batchItems: dataFormat[] = gh.batches.map((a, i) => ({name: a.batchId, id: i, data: a}))
    const gaItems: dataFormat[] = gh.growingAreas.map((g, i) => ({name: g.growingAreaName, id: i, data: g}))

    const {setForm, form} = useForm<{
        plantType: string,
        growthStage: string,
        status: string,
        selectedGA: dataFormat|null
    }>({
        plantType: "",
        growthStage: "",
        status: "",
        selectedGA: null,
    })
    
    async function changeBatch(action?: "harvest" | "terminate"){
        const valid = validateInput()
        if(!valid) return

        user.setLoading(true)
        let res: APIResult<{success: boolean, msg: string}> = {success: false, msg: ""}

        if(!edit){
            res = await createBatch(user.accessToken, {
               plantType: form.plantType,
               growthStage: form.growthStage,
               status: form.growthStage,
               growingAreaID: (form.selectedGA!.data as GAGrowingArea).growingAreaId
            })
        }else{
            res = await updateBatch(user.accessToken, {
               batchID: (selectedBatchItem!.data as BABatch).batchId,
               action: action!
            })
        }

        if(!res.success) {
            alert(res.msg); 
        }else{
            setOpend(false)
            gh.setUpdate(Math.random())
        }
        user.setLoading(false)
    }

    function validateInput(){
        if((!form.plantType || !form.growthStage || !form.status || !form.selectedGA) && !edit){
            alert("Enter values for all fields")
            return false
        }
        if(!selectedBatchItem && edit){
            alert("Select a batch to edit first")
            return false
        }
        return true
    }

    return (
        <div onClick={e => e.stopPropagation()} className="w-[80%] max-w-120">
            <Panel styles="p-3  flex flex-col gap-3">
                <IconTitle
                        title={edit ? "Edit Batch" : "Create Batch"}
                        icon={<TbEdit />}
                />
                <div className="flex gap-2 items-center mt-2 justify-between">
                        <p className="text-xs text-subtext1">
                            Edit existing batch:
                        </p>
                        <div className="flex gap-2">
                            <XsButton
                                name="Yes"
                                highlight={edit}
                                onClick={() => setEdit(true)}
                                animate={false}
                            />
                            <XsButton
                                name="No"
                                highlight={!edit}
                                onClick={() => {
                                    setEdit(false);
                                    setSelectedBatchItem(null)
                                }}
                                animate={false}
                            />
                        </div>
                </div>
                <hr className="text-border"/>
                {edit &&
                    <>
                        <div className="flex gap-2 items-center justify-between">
                                <p className="text-xs text-subtext1">
                                    Select Batch To Edit:
                                </p>
                                <Dropdown
                                    items={batchItems}
                                    setSelectedItem={id => setSelectedBatchItem(batchItems.find(i => i.id == id)!)}
                                    selectedItem={selectedBatchItem}
                                    defaultText="Select"
                                    showIcon={true}
                                />
                        </div>
                        <hr className="text-border"/>
                    </>
                }
                {!edit &&
                    <>
                        <div className="flex flex-col gap-3">
                            <TextBox
                                name="Plant Type"
                                charLimit={20}
                                value={form.plantType}
                                setValue={(v) => setForm("plantType", v)}
                                placeHolder={selectedBatchItem ? `${(selectedBatchItem.data as GAGrowingArea).growingAreaName}` : ""}
                            />
                            <TextBox
                                name="Growth Stage"
                                charLimit={20}
                                value={form.growthStage}
                                setValue={(v) => setForm("growthStage", v)}
                                placeHolder={selectedBatchItem ? `${(selectedBatchItem.data as GAGrowingArea).farmLevel}` : ""}
                            />
                            <TextBox
                                name="Status"
                                charLimit={10}
                                value={form.status}
                                setValue={(v) => setForm("status", v)}
                                placeHolder={selectedBatchItem ? `${(selectedBatchItem.data as GAGrowingArea).slotCount}` : ""}
                            />
                            <div className="flex gap-2 flex-col  justify-between">
                                <p className="text-xs text-subtext1 font-semibold">
                                    Select Growing Area:
                                </p>
                                <Dropdown
                                    items={gaItems}
                                    setSelectedItem={id => setForm("selectedGA", (gaItems.find(i => i.id == id)!))}
                                    selectedItem={form.selectedGA}
                                    defaultText="Select Growing Area"
                                    showIcon={true}
                                />
                            </div>
                        </div>
                    </>
                }
                <div className="flex gap-3 mt-3">
                    <Button
                        name="Close"
                        highlight={false}
                        onSubmit={() => {
                            setOpend(false)
                            setSelectedBatchItem(null)
                        }}
                        styles={{ noAnimation: true}}
                    />
                    {selectedBatchItem && edit &&
                        <>
                            <Button
                                name="Terminate"
                                highlight={false}
                                onSubmit={() => changeBatch("terminate")}
                                styles={{ noAnimation: true}}
                            />
                            <Button
                                name="Harvest"
                                highlight={true}
                                onSubmit={() => changeBatch("harvest")}
                                styles={{ noAnimation: true}}
                            />
                        </>
                    }
                    {!edit && 
                        <Button
                            name="Create Batch"
                            highlight={true}
                            onSubmit={() => changeBatch()}
                            styles={{ noAnimation: true}}
                        />
                    }
                </div>
            </Panel>
        </div>
    )
}
