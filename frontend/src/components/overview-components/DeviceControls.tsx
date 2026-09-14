import { useEffect, useState } from "react"
import IconTitle from "../primatives/IconTitle"
import Panel from "../primatives/Panel"
import { GoGear } from "react-icons/go"
import { getPowerDevices, setPowerDeviceState } from "../../util/api-service-layer"
import type { PowerDevice } from "../../util/types"

export default function DeviceControls() {
    const [devices, setDevices] = useState<PowerDevice[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState("")
    const [busy, setBusy] = useState<number | null>(null)

    const refresh = async () => {
        const result = await getPowerDevices()
        if (result.success) {
            setDevices(result.data || [])
            setError("")
        } else setError(result.msg)
        setLoading(false)
    }

    useEffect(() => {
        refresh()
        const timer = window.setInterval(refresh, 10_000)
        return () => window.clearInterval(timer)
    }, [])

    const toggle = async (device: PowerDevice) => {
        if (device.is_on === null) return
        setBusy(device.device_id)
        const result = await setPowerDeviceState(device.device_id, device.is_on ? "OFF" : "ON")
        setBusy(null)
        if (!result.success) setError(result.msg)
        await refresh()
    }

    return (
        <Panel styles="p-3 px-4 flex flex-col gap-4">
            <div className="flex items-center justify-between">
                <IconTitle title="Powerboard" icon={<GoGear />} />
                <button onClick={refresh} className="text-xs border border-border rounded-md px-2 py-1 text-subtext1 hover:cursor-pointer">Refresh</button>
            </div>
            {loading && <p className="text-sm text-subtext2">Connecting to powerboard…</p>}
            {error && <p className="text-sm text-high">Powerboard: {error}</p>}
            <div className="flex flex-col gap-2">
                {devices.map(device => (
                    <div key={device.device_id} className="flex items-center justify-between bg-panel2 p-2 border border-border rounded-lg px-3">
                        <div>
                            <p className="text-subtext1 text-sm">{device.name}</p>
                            <p className="text-subtext3 text-xs">{device.state === "NOT CONFIGURED" ? "Not configured" : device.state}</p>
                        </div>
                        <button
                            disabled={busy === device.device_id || device.is_on === null}
                            onClick={() => toggle(device)}
                            className={`border rounded-md px-3 py-1 text-xs ${device.is_on ? "border-highlight text-highlight" : "border-border2 text-subtext2"} disabled:opacity-50`}
                        >
                            {busy === device.device_id ? "Working…" : device.is_on ? "Turn off" : "Turn on"}
                        </button>
                    </div>
                ))}
            </div>
        </Panel>
    )
}
