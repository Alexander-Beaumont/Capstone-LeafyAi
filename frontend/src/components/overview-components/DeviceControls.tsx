import Panel from "../primatives/Panel"
import Switch from "../primatives/Switch"
import { useState } from "react"

export default function DeviceControls() {
    const [ticked, setTicked] = useState(false)

    return (
        <Panel styles="p-3 px-4 flex flex-col gap-5">
            <p className="text-md font-semibold text-title">
                Device Control
            </p>
            <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between bg-panel2 p-2 border border-border rounded-lg px-3">
                    <p className="text-subtext1">
                        Pump
                    </p>
                    <Switch
                        ticked={ticked}
                        setTicked={setTicked}
                    />
                </div>
                <div className="flex items-center justify-between bg-panel2 p-2 border border-border rounded-lg px-3">
                    <p className="text-subtext1">
                        Lights
                    </p>
                    <Switch
                        ticked={ticked}
                        setTicked={setTicked}
                    />
                </div>
                <div className="flex items-center justify-between bg-panel2 p-2 border border-border rounded-lg px-3">
                    <p className="text-subtext1">
                        Fans
                    </p>
                    <Switch
                        ticked={ticked}
                        setTicked={setTicked}
                    />
                </div>
                <div className="flex items-center justify-between bg-panel2 p-2 border border-border rounded-lg px-3">
                    <p className="text-subtext1">
                        Doser
                    </p>
                    <Switch
                        ticked={ticked}
                        setTicked={setTicked}
                    />
                </div>
            </div>
        </Panel>
    )
}
