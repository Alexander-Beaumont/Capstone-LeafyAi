import Panel from "../primatives/Panel"
import Button from "../primatives/Button"
import Dropdown from "../primatives/Dropdown"
import { type dataFormat } from "../primatives/Dropdown"
import IconTitle from "../primatives/IconTitle"
import TextBox from "../primatives/Textbox"
import { useState } from "react"
import { GaGrowingAreas } from "../../util/constants"
import { TbEdit } from "react-icons/tb"
import XsButton from "../primatives/XsButton"
import type { GAGrowingArea } from "../../util/types"
import useForm from "../hooks/useFrom"

interface Props{
    opened: boolean
    setOpend: (state: boolean) => void
}

export default function GaEditCard({setOpend} : Props) {
    const [yes, setYes] = useState(false)
    const [selectedItem, setSelectedItem] = useState<dataFormat|null>(null)
    const items: dataFormat[] = GaGrowingAreas.map((g, i) => ({name: g.growingAreaName, id: i, data: g}))

    const {setForm, form} = useForm({
        growingAreaName: "",
        FarmLevel: "",
        SlotCount: ""
    })

    return (
        <div onClick={e => e.stopPropagation()} className="w-[80%] max-w-120">
            <Panel styles="p-3  flex flex-col gap-3">
                <IconTitle
                        title="Edit Growing Areas"
                        icon={<TbEdit />}
                />
                <div className="flex gap-2 items-center mt-2 justify-between">
                        <p className="text-xs text-subtext1">
                            Edit existing growing area:
                        </p>
                        <div className="flex gap-2">
                            <XsButton
                                name="Yes"
                                highlight={yes}
                                onClick={() => setYes(true)}
                                animate={false}
                            />
                            <XsButton
                                name="No"
                                highlight={!yes}
                                onClick={() => {
                                    setYes(false);
                                    setSelectedItem(null)
                                }}
                                animate={false}
                            />
                        </div>
                </div>
                {yes && 
                <>
                    <hr className="text-border"/>
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
                </>
                }
                <hr className="text-border"/>
                <div className="flex flex-col gap-3">
                    <TextBox
                        name="Growing Area Name"
                        charLimit={20}
                        value={form.growingAreaName}
                        setValue={(v) => setForm("growingAreaName", v)}
                        placeHolder={selectedItem ? (selectedItem.data as GAGrowingArea).growingAreaName : ""}
                    />
                    <TextBox
                        name="Farm Level"
                        charLimit={2}
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
                <div className="flex gap-3 mt-3">
                    <Button
                        name="Close"
                        highlight={false}
                        onSubmit={() => {
                            setOpend(false)
                            setYes(false)
                            setSelectedItem(null)
                        }}
                        styles={{ noAnimation: true}}
                    />
                    <Button
                        name="Delete"
                        highlight={false}
                        onSubmit={() => {}}
                        styles={{ noAnimation: true}}
                    />
                    {!yes &&
                        <Button
                            name="Create New GA"
                            highlight={true}
                            onSubmit={() => {}}
                            styles={{ noAnimation: true}}
                        />
                    }
                    {yes &&
                        <Button
                            name="Update"
                            highlight={true}
                            onSubmit={() => {}}
                            styles={{ noAnimation: true}}
                        />
                    }
                </div>
            </Panel>
        </div>
    )
}
