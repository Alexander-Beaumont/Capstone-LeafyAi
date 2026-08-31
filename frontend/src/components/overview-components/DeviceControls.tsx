import useForm from "../hooks/useFrom"
import IconTitle from "../primatives/IconTitle"
import Panel from "../primatives/Panel"
import Switch from "../primatives/Switch"
import { GoGear } from "react-icons/go";

export default function DeviceControls() {
    const {form, setForm, resetForm} = useForm({
        pump: false,
        lights: false,
        fans: false,
        doser: false
    })

    return (
        <Panel styles="p-3 px-4 flex flex-col gap-5">
            <div className="flex  items-center justify-between">
                <IconTitle
                    title="Device Control"
                    icon={<GoGear />}
                />
                <button className="bg-panel2 border border-high text-high text-sm font-semibold px-3 rounded-md
                    hover:cursor-pointer hover:rounded-lg transition-all duration-200 hover:italic"
                    onClick={() => resetForm()}>
                    E-Stop
                </button>
            </div>
            <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between bg-panel2 p-2 border border-border rounded-lg px-3">
                    <p className="text-subtext1">
                        Pump
                    </p>
                    <Switch
                        ticked={form.pump}
                        setTicked={() => setForm("pump", !form.pump)}
                    />
                </div>
                <div className="flex items-center justify-between bg-panel2 p-2 border border-border rounded-lg px-3">
                    <p className="text-subtext1">
                        Lights
                    </p>
                    <Switch
                        ticked={form.lights}
                        setTicked={() => setForm("lights", !form.lights)}
                    />
                </div>
                <div className="flex items-center justify-between bg-panel2 p-2 border border-border rounded-lg px-3">
                    <p className="text-subtext1">
                        Fans
                    </p>
                    <Switch
                        ticked={form.fans}
                        setTicked={() => setForm("fans", !form.fans)}
                    />
                </div>
                <div className="flex items-center justify-between bg-panel2 p-2 border border-border rounded-lg px-3">
                    <p className="text-subtext1">
                        Doser
                    </p>
                    <Switch
                        ticked={form.doser}
                        setTicked={() => setForm("doser", !form.doser)}
                    />
                </div>
            </div>
        </Panel>
    )
}
