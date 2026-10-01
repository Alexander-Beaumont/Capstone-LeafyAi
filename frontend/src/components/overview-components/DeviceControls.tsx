import { useContext, useState } from "react"
import IconTitle from "../primatives/IconTitle"
import Panel from "../primatives/Panel"
import Switch from "../primatives/Switch"
import ConfirmDialog from "../primatives/ConfirmDialog"
import { GoGear } from "react-icons/go";
import { FarmOverviewContext } from "../../providers/FarmOverviewProvider"
import { userContext } from "../../providers/UserProvider"
import { setDeviceState } from "../../util/api-service-layer"
import { CONTROLLED_DEVICES, findDevice, isControllable, isOn } from "../../util/device-controls"
import type { PowerboardDevice } from "../../util/types"

export default function DeviceControls() {
    const user = useContext(userContext)
    const overview = useContext(FarmOverviewContext)
    const [busyId, setBusyId] = useState<number | "stop" | null>(null)
    const [error, setError] = useState("")
    const [confirmStop, setConfirmStop] = useState(false)

    const offline = overview.devices.length === 0 || overview.devices.every(device => !isControllable(device))

    async function toggleDevice(device: PowerboardDevice | undefined, currentlyOn: boolean) {
        if (!isControllable(device) || device == null || busyId != null) return
        setBusyId(device.device_id)
        setError("")
        const res = await setDeviceState(user.accessToken, device.device_id, currentlyOn ? "OFF" : "ON")
        setBusyId(null)
        if (!res.success) {
            setError(res.msg)
            return
        }
        overview.setUpdate(Math.random())
    }

    async function emergencyStop() {
        if (busyId != null) return
        setBusyId("stop")
        setError("")
        const results = await Promise.all(
            CONTROLLED_DEVICES.map(device => setDeviceState(user.accessToken, device.id, "OFF"))
        )
        setBusyId(null)
        setConfirmStop(false)
        const failed = results.find(result => !result.success)
        if (failed) setError(failed.msg)
        overview.setUpdate(Math.random())
    }

    function controlRow(key: number, label: string, ticked: boolean, enabled: boolean, onToggle: () => void) {
        const rowBusy = busyId === key
        return (
            <div key={key} className="flex w-full items-center justify-between gap-2 border border-border bg-panel2 px-2 py-1.5 rounded-lg">
                <p className="text-sm text-subtext1">
                    {label}
                </p>
                <div className={enabled && !rowBusy ? "" : "opacity-40 pointer-events-none"} title={enabled ? undefined : "Device offline"}>
                    <Switch
                        ticked={ticked}
                        setTicked={() => {
                            if (rowBusy || busyId != null || !enabled) return
                            onToggle()
                        }}
                    />
                </div>
            </div>
        )
    }

    return (
        <Panel styles="w-full p-3 px-4 flex flex-col gap-5">
            <div className="flex items-center justify-between">
                <IconTitle
                    title="Device Control"
                    icon={<GoGear />}
                />
                <div className="flex items-center gap-2">
                    {overview.loading && overview.devices.length === 0 ?
                        <p className="text-xs text-subtext3">Loading…</p>
                    : offline ?
                        <p className="text-xs text-subtext3">Powerboard offline</p>
                    : null}
                    <button className="bg-panel2 border border-high text-high text-xs font-semibold px-3 rounded-md
                        hover:cursor-pointer hover:rounded-lg transition-all duration-200 hover:italic disabled:opacity-40 disabled:cursor-not-allowed"
                        disabled={busyId === "stop"}
                        onClick={() => setConfirmStop(true)}>
                        {busyId === "stop" ? "Stopping…" : "E-Stop"}
                    </button>
                </div>
            </div>
            {error ? <p className="text-xs text-high">{error}</p> : null}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
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
            <ConfirmDialog
                open={confirmStop}
                title="Emergency stop?"
                text="This turns off every controlled outlet."
                confirm="E-Stop"
                busy={busyId === "stop"}
                onConfirm={() => { void emergencyStop() }}
                onClose={() => setConfirmStop(false)}
            />
        </Panel>
    )
}
