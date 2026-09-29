import { useContext, useEffect, useState } from "react"
import Panel from "../primatives/Panel"
import IconTitle from "../primatives/IconTitle"
import { LuList } from "react-icons/lu"
import { FarmOverviewContext } from "../../providers/FarmOverviewProvider"
import { userContext } from "../../providers/UserProvider"
import { getSensorReadings } from "../../util/api-service-layer"
import { formatTimestamp, localInputToIso, readingNumber } from "../../util/operator"
import type { SensorReadingRecord } from "../../util/types"
import Pager from "./Pager"
import DateTimeField from "../primatives/DateTimeField"
import { sensorLabel } from "../../util/sensor-readings"

const QUALITIES = ["valid", "unverified", "suspect"]
const LIMIT = 20

export default function SensorReadingsPanel() {
    const user = useContext(userContext)
    const overview = useContext(FarmOverviewContext)
    const sensors = overview.farmState?.devices.flatMap(device => device.sensors) ?? []
    const [selected, setSelected] = useState<string[]>([])
    const [qualities, setQualities] = useState<string[]>([])
    const [start, setStart] = useState("")
    const [end, setEnd] = useState("")
    const [offset, setOffset] = useState(0)
    const [count, setCount] = useState(0)
    const [rows, setRows] = useState<SensorReadingRecord[]>([])
    const [error, setError] = useState("")
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (!user.accessToken || overview.farmId == null) return
        let cancelled = false
        const token = user.accessToken
        const farmId = overview.farmId
        const run = async () => {
            const result = await getSensorReadings(token, farmId, {
                sensors: selected.join(","),
                quality: qualities.join(","),
                start: localInputToIso(start),
                end: localInputToIso(end),
                limit: LIMIT,
                offset,
            })
            if (cancelled) return
            setLoading(false)
            if (!result.success || !result.data) {
                setRows([])
                setCount(0)
                setError(result.msg)
                return
            }
            setError("")
            setRows(result.data.results)
            setCount(result.data.count)
        }
        run()
        return () => {
            cancelled = true
        }
    }, [user.accessToken, overview.farmId, selected, qualities, start, end, offset])

    function toggle(list: string[], value: string, setList: (next: string[]) => void) {
        setList(list.includes(value) ? list.filter(item => item !== value) : [...list, value])
    }

    return (
        <Panel styles="w-full p-3 flex flex-col gap-4">
            <IconTitle title="Sensor readings" icon={<LuList size={16} />} />
            {!overview.farmId ?
                <p className="text-sm text-subtext3">Select a farm to load readings.</p>
            : <>
                <div className="flex flex-wrap gap-2">
                    {sensors.map(sensor => (
                        <button
                            key={sensor.sensor_id}
                            type="button"
                            className={`text-xs px-2 py-1 rounded-md border ${selected.includes(sensor.sensor_slug) ? "bg-highlight text-btn-text border-highlight" : "bg-panel2 text-subtext2 border-border"}`}
                            onClick={() => {
                                toggle(selected, sensor.sensor_slug, setSelected)
                                setOffset(0)
                            }}
                        >
                            {sensorLabel(sensor.sensor_slug)}
                        </button>
                    ))}
                </div>
                <div className="flex flex-wrap gap-2">
                    {QUALITIES.map(quality => (
                        <button
                            key={quality}
                            type="button"
                            className={`text-xs px-2 py-1 rounded-md border ${qualities.includes(quality) ? "bg-highlight text-btn-text border-highlight" : "bg-panel2 text-subtext2 border-border"}`}
                            onClick={() => {
                                toggle(qualities, quality, setQualities)
                                setOffset(0)
                            }}
                        >
                            {quality}
                        </button>
                    ))}
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                    <DateTimeField name="Start" value={start} setValue={value => { setStart(value); setOffset(0) }} />
                    <DateTimeField name="End" value={end} setValue={value => { setEnd(value); setOffset(0) }} />
                </div>
                {error ? <p className="text-xs text-high">{error}</p> : null}
                {loading && rows.length === 0 ? <div className="h-24 bg-panel2 animate-pulse rounded-md" /> : null}
                {rows.length === 0 && !loading ?
                    <p className="text-sm text-subtext3">No readings match these filters.</p>
                :
                    <div className="overflow-x-auto">
                        <table className="w-full text-xs text-left">
                            <thead className="text-subtext3">
                                <tr>
                                    <th className="py-1 pr-3 font-medium">Sensor</th>
                                    <th className="py-1 pr-3 font-medium">Value</th>
                                    <th className="py-1 pr-3 font-medium">Quality</th>
                                    <th className="py-1 font-medium">Measured</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows.map(row => {
                                    const value = readingNumber(row.value)
                                    return (
                                        <tr key={row.id} className="border-t border-border text-subtext1">
                                            <td className="py-2 pr-3">{sensorLabel(row.sensor_slug)}</td>
                                            <td className="py-2 pr-3">{value == null ? row.value : value} {row.unit}</td>
                                            <td className="py-2 pr-3">{row.quality_status}</td>
                                            <td className="py-2">{formatTimestamp(row.measured_at)}</td>
                                        </tr>
                                    )
                                })}
                            </tbody>
                        </table>
                    </div>
                }
                <Pager offset={offset} limit={LIMIT} count={count} onOffset={setOffset} />
            </>}
        </Panel>
    )
}
