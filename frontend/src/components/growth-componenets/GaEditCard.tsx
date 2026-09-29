import Panel from "../primatives/Panel"
import Button from "../primatives/Button"
import Dropdown from "../primatives/Dropdown"
import { type dataFormat } from "../primatives/Dropdown"
import IconTitle from "../primatives/IconTitle"
import TextBox from "../primatives/Textbox"
import { useContext, useState } from "react"
import { TbEdit } from "react-icons/tb"
import XsButton from "../primatives/XsButton"
import type { APIResult, GAGrowingArea } from "../../util/types"
import useForm from "../hooks/useFrom"
import { createGrowingArea, deleteGrowingArea, updateGrowingArea } from "../../util/api-service-layer"
import { userContext } from "../../providers/UserProvider"
import { GrowthHarvestingContext } from "../../providers/GrowthHarvestProvider"
import { FarmOverviewContext } from "../../providers/FarmOverviewProvider"

interface Props{
    opened: boolean
    setOpend: (state: boolean) => void
}

export default function GaEditCard({setOpend} : Props) {
    const user = useContext(userContext)
    const gh = useContext(GrowthHarvestingContext)
    const overview = useContext(FarmOverviewContext)

    const [editExistingGa, setEditExistingGa] = useState(false)
    const [selectedItem, setSelectedItem] = useState<dataFormat|null>(null)
    const [error, setError] = useState("")
    const items: dataFormat[] = gh.growingAreas.map((g, i) => ({name: g.growingAreaName, id: i, data: g}))

    const {setForm, form} = useForm({
        name: "",
        FarmLevel: "",
        SlotCount: ""
    })

    async function changeGA() {
        const valid = validateInput()
        if(!valid) return

        setError("")
        user.setLoading(true)
        if (overview.farmId == null) {
            setError("Select a farm in the navigation bar.")
            user.setLoading(false)
            return
        }

        let res: APIResult<{success: boolean, msg: string}>

        if(!editExistingGa){
            res = await createGrowingArea(user.accessToken, overview.farmId, {
                name: form.name,
                slotCount: Number(form.SlotCount),
                farmLevel: Number(form.FarmLevel)
            })
        }else{
            res = await updateGrowingArea(user.accessToken, overview.farmId, {
                growingAreaID: `${(selectedItem!.data as GAGrowingArea).growingAreaId}`,
                name: form.name,
                slotCount: Number(form.SlotCount),
                farmLevel: Number(form.FarmLevel)
            })
        }

        if(!res.success) {
            setError(res.msg);
        }else{
            setOpend(false)
            gh.setUpdate(Math.random())
        }
        user.setLoading(false)
    }

    async function deleteGA(){
        if(!selectedItem){
            setError("Select a growing area to delete first")
            return
        }
        if((selectedItem.data as GAGrowingArea).batches.some(b => !b.GrowthAreaEndDate)){
            setError("Can't delete this growing area as there is a active batch occupying it. Move or terminate this batch before deleting the growing area")
            return
        }

        setError("")
        user.setLoading(true)
        if (overview.farmId == null) {
            setError("Select a farm in the navigation bar.")
            user.setLoading(false)
            return
        }
        const res = await deleteGrowingArea(user.accessToken, overview.farmId, (selectedItem.data as GAGrowingArea).growingAreaId)


        if(!res.success) {
            setError(res.msg);
        }else{
            setOpend(false)
            gh.setUpdate(Math.random())
        }
        user.setLoading(false)
    }

    function validateInput(){
        if(Number(form.FarmLevel) < 1 || Number(form.FarmLevel) > 2){
            setError("Farm level can either be 1 or 2")
            return false
        }
        if(!form.name || !form.SlotCount){
            setError("All fields must have a value")
            return false
        }

        if(editExistingGa && !selectedItem){
            setError("Select a growing area first")
            return false
        }
        return true
    }
    
    return (
        <div onClick={e => e.stopPropagation()} className="w-[80%] max-w-120">
            <Panel styles="p-3  flex flex-col gap-3">
                <IconTitle
                        title={editExistingGa ? "Edit Growing Areas" : "Create New Growing Area"}
                        icon={<TbEdit />}
                />
                {error ? <p className="text-xs text-high">{error}</p> : null}
                <div className="flex gap-2 items-center mt-2 justify-between">
                        <p className="text-xs text-subtext1">
                            Edit existing growing area:
                        </p>
                        <div className="flex gap-2">
                            <XsButton
                                name="Yes"
                                highlight={editExistingGa}
                                onClick={() => setEditExistingGa(true)}
                                animate={false}
                            />
                            <XsButton
                                name="No"
                                highlight={!editExistingGa}
                                onClick={() => {
                                    setEditExistingGa(false);
                                    setSelectedItem(null)
                                }}
                                animate={false}
                            />
                        </div>
                </div>
                {editExistingGa && 
                <>
                    <hr className="text-border"/>
                    {items.length == 0 ? 
                        <p className="text-xs text-subtext1">
                            No growing areas exist, create one first...
                        </p> :
                        <div className="flex gap-2 items-center justify-between">
                                <p className="text-xs text-subtext1">
                                    Select Growing Area:
                                </p>
                                <Dropdown
                                    items={items}
                                    setSelectedItem={id => setSelectedItem(items.find(i => i.id == id)!)}
                                    selectedItem={selectedItem}
                                    defaultText="Select"
                                />
                        </div>
                    }
                </>
                }
                <hr className="text-border"/>
                {editExistingGa && items.length == 0 ? "" :
                    <div className="flex flex-col gap-3">
                        <TextBox
                            name="Name"
                            charLimit={20}
                            value={form.name}
                            setValue={(v) => setForm("name", v)}
                            placeHolder={selectedItem ? `${(selectedItem.data as GAGrowingArea).growingAreaName}` : ""}
                        />
                        <TextBox
                            name="Farm Level"
                            charLimit={1}
                            value={form.FarmLevel}
                            setValue={(v) => setForm("FarmLevel", v)}
                            placeHolder={selectedItem ? `${(selectedItem.data as GAGrowingArea).farmLevel}` : ""}
                            numeric={true}
                        />
                        <TextBox
                            name="Slot Count"
                            charLimit={3}
                            value={form.SlotCount}
                            setValue={(v) => setForm("SlotCount", v)}
                            placeHolder={selectedItem ? `${(selectedItem.data as GAGrowingArea).slotCount}` : ""}
                            numeric={true}
                        />
                    </div>
                }
                <div className="flex gap-3 mt-3">
                    <Button
                        name="Close"
                        highlight={false}
                        onSubmit={() => {
                            setOpend(false)
                            setEditExistingGa(false)
                            setSelectedItem(null)
                        }}
                        styles={{ noAnimation: true}}
                    />
                    {!editExistingGa &&
                        <Button
                            loading={user.loading}
                            name="Create New GA"
                            highlight={true}
                            onSubmit={() => changeGA()}
                            styles={{ noAnimation: true}}
                        />
                    }
                    {editExistingGa &&
                        <>
                            <Button
                                name="Delete"
                                highlight={false}
                                onSubmit={() => deleteGA()}
                                styles={{ noAnimation: true}}
                            />
                            <Button
                                loading={user.loading}
                                name="Update"
                                highlight={true}
                                onSubmit={() => changeGA()}
                                styles={{ noAnimation: true}}
                            />
                        </>
                    }
                </div>
            </Panel>
        </div>
    )
}
