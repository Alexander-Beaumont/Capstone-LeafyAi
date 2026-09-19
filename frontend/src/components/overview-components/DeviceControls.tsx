import { useContext } from "react"
import IconTitle from "../primatives/IconTitle"
import Panel from "../primatives/Panel"
import Switch from "../primatives/Switch"
import { GoGear } from "react-icons/go";
import { FarmOverviewContext } from "../../providers/FarmOverviewProvider"
import { userContext } from "../../providers/UserProvider"
import { setDeviceState } from "../../util/api-service-layer"
import { CONTROLLED_DEVICES, findDevice, isControllable, isOn } from "../../util/device-controls"
import type { PowerboardDevice } from "../../util/types"

export default function DeviceControls() {
    const user = useContext(userContext)
    const overview = useContext(FarmOverviewContext)

    const offline = overview.devices.length === 0 || overview.devices.every(device => !isControllable(device))
    const controlsBusy = overview.loading || user.loading

    async function toggleDevice(device: PowerboardDevice | undefined, currentlyOn: boolean) {
        if (!isControllable(device) || device == null) return
        user.setLoading(true)
        const res = await setDeviceState(user.accessToken, device.device_id, currentlyOn ? "OFF" : "ON")
        if (!res.success) {
            alert(res.msg)
        } else {
            overview.setUpdate(Math.random())
        }
        user.setLoading(false)
    }

    async function emergencyStop() {
        user.setLoading(true)
        const results = await Promise.all(
            CONTROLLED_DEVICES.map(device => setDeviceState(user.accessToken, device.id, "OFF"))
        )
        const failed = results.find(result => !result.success)
        if (failed) {
            alert(failed.msg)
        }
        overview.setUpdate(Math.random())
        user.setLoading(false)
    }

    function controlRow(key: number, label: string, ticked: boolean, enabled: boolean, onToggle: () => void) {
        return (
            <div key={key} className="flex items-center justify-between bg-panel2 p-2 border border-border rounded-lg px-3">
                <p className="text-subtext1">
                    {label}
                </p>
                <div className={enabled && !controlsBusy ? "" : "opacity-40 pointer-events-none"} title={enabled ? undefined : "Device offline"}>
                    <Switch
                        ticked={ticked}
                        setTicked={() => {
                            if (controlsBusy || !enabled) return
                            onToggle()
                        }}
                    />
                </div>
            </div>
        )
    }

    return (
        <Panel styles="p-3 px-4 flex flex-col gap-5">
            <div className="flex  items-center justify-between">
                <IconTitle
                    title="Device Control"
                    icon={<GoGear />}
                />
                <button className="bg-panel2 border border-high text-high text-sm font-semibold px-3 rounded-md
                    hover:cursor-pointer hover:rounded-lg transition-all duration-200 hover:italic disabled:opacity-40 disabled:cursor-not-allowed"
                    disabled={controlsBusy}
                    onClick={() => emergencyStop()}>
                    E-Stop
                </button>
            </div>
            {overview.loading && overview.devices.length === 0 ?
                <p className="text-xs text-subtext3">
                    Loading…
                </p>
            : offline ?
                <p className="text-xs text-subtext3">
                    Powerboard offline
                </p>
            : null}
            <div className="flex flex-col gap-3">
                {CONTROLLED_DEVICES.map(controlled => {
                    const device = findDevice(overview.devices, controlled.id)
                    return controlRow(
                        controlled.id,
                        controlled.name,
                        isOn(device),
                        isControllable(device),
                        () => toggleDevice(device, isOn(device)),
                    )
                })}
            </div>
        </Panel>
    )
}
