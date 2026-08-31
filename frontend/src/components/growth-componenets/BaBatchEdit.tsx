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
import { BATCH_STATUS, GROWTH_STAGES } from "../../util/constants"

interface Props{
    opened: boolean
    setOpend: (state: boolean) => void
}

export default function BaBatchEdit({setOpend} : Props) {
    const user = useContext(userContext)
    const gh = useContext(GrowthHarvestingContext)

    const [edit, setEdit] = useState(false)
    const [openId, setOpenId] = useState(0)
    const [selectedBatchItem, setSelectedBatchItem] = useState<dataFormat|null>(null)

    const batchItems: dataFormat[] = gh.batches.filter(b => b.status == "Growing").map((a, i) => ({name: a.batchId, id: i, data: a}))
    const gaItems: dataFormat[] = gh.growingAreas.map((g, i) => ({name: g.growingAreaName, id: i, data: g}))

    const {setForm, form} = useForm<{
        plantType: string,
        growthStage: dataFormat|null
        status: dataFormat|null
        selectedGA: dataFormat|null
    }>({
        plantType: "",
        growthStage: null,
        status: null,
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
               growthStage: form.growthStage!.name,
               status: form.growthStage!.name,
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
        if((!form.plantType || !form.growthStage?.name || !form.status?.name || !form.selectedGA) && !edit){
            alert("Enter values for all fields")
            return false
        }
        if(!selectedBatchItem && edit){
            alert("Select a batch to edit first")
            return false
        }
        if(!edit && (form.selectedGA!.data as GAGrowingArea).batches.some(b => !b.GrowthAreaEndDate)){
            alert("Select a growing area that does not currently have a active batch")
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
                                   {batchItems.length > 0 ? 
                                    "Select Batch To Edit:" :
                                    "No active batches to edit, create one first..."
                                   } 
                                </p>
                                {batchItems.length > 0 && 
                                    <Dropdown
                                        items={batchItems}
                                        setSelectedItem={id => setSelectedBatchItem(batchItems.find(i => i.id == id)!)}
                                        selectedItem={selectedBatchItem}
                                        defaultText="Select"
                                        showIcon={true}
                                    />
                                }
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
                            <div className="flex gap-2 flex-col  justify-between">
                                <p className="text-xs text-subtext1 font-semibold">
                                    Select Growth Stage:
                                </p>
                                <Dropdown
                                    items={GROWTH_STAGES}
                                    setSelectedItem={id => setForm("growthStage", (GROWTH_STAGES.find(i => i.id == id)!))}
                                    selectedItem={form.growthStage}
                                    defaultText="Select Growth Stage"
                                    showIcon={true}
                                     onBtnClick={() => setOpenId(1)}
                                    blur={openId != 1}
                                />
                            </div>
                            <div className="flex gap-2 flex-col  justify-between">
                                <p className="text-xs text-subtext1 font-semibold">
                                    Status:
                                </p>
                                <Dropdown
                                    items={BATCH_STATUS}
                                    setSelectedItem={id => setForm("status", (BATCH_STATUS.find(i => i.id == id)!))}
                                    selectedItem={form.status}
                                    defaultText="Select Status"
                                    showIcon={true}
                                    onBtnClick={() => setOpenId(2)}
                                    blur={openId != 2}
                                />
                            </div>
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
                                    onBtnClick={() => setOpenId(3)}
                                    blur={openId != 3}
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
