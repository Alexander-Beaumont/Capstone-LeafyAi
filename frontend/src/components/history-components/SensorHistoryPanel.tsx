import { useContext, useEffect, useState } from "react"
import Panel from "../primatives/Panel"
import IconTitle from "../primatives/IconTitle"
import Dropdown, { type dataFormat } from "../primatives/Dropdown"
import { LuActivity } from "react-icons/lu"
import { FarmOverviewContext } from "../../providers/FarmOverviewProvider"
import { userContext } from "../../providers/UserProvider"
import { getSensorHistory } from "../../util/api-service-layer"
import { formatTimestamp, localInputToIso } from "../../util/operator"
import type { SensorHistory } from "../../util/types"
import Sparkline from "./Sparkline"

const presets: dataFormat[] = [
    { id: 0, name: "1h", data: "1h" },
    { id: 1, name: "24h", data: "24h" },
    { id: 2, name: "7d", data: "7d" },
    { id: 3, name: "custom", data: "custom" },
]

const buckets: dataFormat[] = [
    { id: 0, name: "default", data: "" },
    { id: 1, name: "5m", data: "5m" },
    { id: 2, name: "15m", data: "15m" },
    { id: 3, name: "1h", data: "1h" },
]

export default function SensorHistoryPanel() {
    const user = useContext(userContext)
    const overview = useContext(FarmOverviewContext)
    const sensors = overview.farmState?.devices.flatMap(device => device.sensors) ?? []
    const [preset, setPreset] = useState(presets[1])
    const [bucket, setBucket] = useState(buckets[0])
    const [selected, setSelected] = useState<string[]>([])
    const [start, setStart] = useState("")
    const [end, setEnd] = useState("")
    const [history, setHistory] = useState<SensorHistory | null>(null)
    const [error, setError] = useState("")

    const needsStart = preset.data === "custom" && !start

    useEffect(() => {
        if (!user.accessToken || overview.farmId == null || needsStart) return
        let cancelled = false
        const token = user.accessToken
        const farmId = overview.farmId
        const run = async () => {
            const result = await getSensorHistory(token, farmId, {
                preset: String(preset.data),
                sensors: selected.join(","),
                bucket: bucket.data ? String(bucket.data) : undefined,
                start: preset.data === "custom" ? localInputToIso(start) : undefined,
                end: preset.data === "custom" ? localInputToIso(end) : undefined,
            })
            if (cancelled) return
            if (!result.success || !result.data) {
                setHistory(null)
                setError(result.msg)
                return
            }
            setError("")
            setHistory(result.data)
        }
        run()
        return () => {
            cancelled = true
        }
    }, [user.accessToken, overview.farmId, preset, bucket, selected, start, end, needsStart])

    function toggleSlug(slug: string) {
        setSelected(current => current.includes(slug) ? current.filter(item => item !== slug) : [...current, slug])
    }

    return (
        <Panel styles="w-full p-3 flex flex-col gap-4">
            <IconTitle title="Sensor history" icon={<LuActivity size={16} />} />
            {!overview.farmId ?
                <p className="text-sm text-subtext3">Select a farm to load history.</p>
            : <>
                <div className="flex flex-wrap gap-3">
                    <Dropdown items={presets} selectedItem={preset} setSelectedItem={id => setPreset(presets[id])} showIcon divStyles="w-28" />
                    <Dropdown items={buckets} selectedItem={bucket} setSelectedItem={id => setBucket(buckets[id])} showIcon divStyles="w-28" />
                </div>
                {preset.data === "custom" ?
                    <div className="grid gap-3 sm:grid-cols-2">
                        <label className="flex flex-col gap-1 text-xs text-subtext1">
                            Start
                            <input className="h-7 rounded-md bg-panel2 outline-1 outline-border2 px-2" type="datetime-local" value={start} onChange={event => setStart(event.target.value)} />
                        </label>
                        <label className="flex flex-col gap-1 text-xs text-subtext1">
                            End
                            <input className="h-7 rounded-md bg-panel2 outline-1 outline-border2 px-2" type="datetime-local" value={end} onChange={event => setEnd(event.target.value)} />
                        </label>
                    </div>
                : null}
                <div className="flex flex-wrap gap-2">
                    {sensors.map(sensor => (
                        <button
                            key={sensor.sensor_id}
                            type="button"
                            className={`text-xs px-2 py-1 rounded-md border ${selected.includes(sensor.sensor_slug) ? "bg-highlight text-btn-text border-highlight" : "bg-panel2 text-subtext2 border-border"}`}
                            onClick={() => toggleSlug(sensor.sensor_slug)}
                        >
                            {sensor.sensor_slug}
                        </button>
                    ))}
                </div>
                {needsStart ? <p className="text-xs text-high">Choose a start time for a custom range.</p> : null}
                {error && !needsStart ? <p className="text-xs text-high">{error}</p> : null}
                {!needsStart && !error && !history ? <div className="h-24 bg-panel2 animate-pulse rounded-md" /> : null}
                {history && history.series.length === 0 ?
                    <p className="text-sm text-subtext3">No readings in this range.</p>
                : null}
                {history?.series.map(series => {
                    const latest = series.points[series.points.length - 1]
                    return (
                        <div key={series.sensor_id} className="border border-border rounded-lg p-3 flex flex-col gap-2">
                            <div className="flex items-baseline justify-between gap-2">
                                <p className="text-sm text-title font-semibold">{series.sensor_slug}</p>
                                <p className="text-xs text-subtext3">
                                    {latest ? `${latest.latest} ${series.unit}` : series.unit}
                                </p>
                            </div>
                            <Sparkline values={series.points.map(point => point.average)} />
                            {latest ?
                                <p className="text-xs text-subtext3">
                                    {formatTimestamp(latest.timestamp)} · min {latest.minimum} · max {latest.maximum} · n {latest.sample_count}
                                </p>
                            : null}
                        </div>
                    )
                })}
            </>}
        </Panel>
    )
}
