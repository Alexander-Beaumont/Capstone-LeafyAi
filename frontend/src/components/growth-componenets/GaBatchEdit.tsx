import Panel from "../primatives/Panel"
import Button from "../primatives/Button"
import Dropdown from "../primatives/Dropdown"
import { type dataFormat } from "../primatives/Dropdown"
import IconTitle from "../primatives/IconTitle"
import { useState } from "react"
import { TbEdit } from "react-icons/tb"

interface Props{
    opened: boolean
    setOpend: (state: boolean) => void
}

export default function GaBatchEdit({setOpend} : Props) {

    const [selectedItem, setSelectedItem] = useState<dataFormat|null>(null)
     const items: dataFormat[] = [].map((g, i) => ({name: g.growingAreaName, id: i, data: g}))

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
                        onSubmit={() => {}}
                        styles={{ noAnimation: true}}
                    />
                </div>
            </Panel>
        </div>
    )
}
