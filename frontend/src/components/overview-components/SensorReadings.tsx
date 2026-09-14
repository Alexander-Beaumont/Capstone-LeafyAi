import { useContext, useEffect, useMemo, useState } from "react"
import InformationPanel from "../primatives/InformationPanel"
import Panel from "../primatives/Panel"
import IconTitle from "../primatives/IconTitle"
import { MdSensors } from "react-icons/md"
import { userContext } from "../../providers/UserProvider"
import { getSensorReadings, getSensors } from "../../util/api-service-layer"
import type { Sensor, SensorReading } from "../../util/types"

const labels: Record<string, string> = {
    ambient_temp: "Air Temperature",
    humidity: "Humidity",
    ph: "pH",
    ec: "EC",
    water_temp: "Water Temperature",
    dew_point: "Dew Point",
    water_level: "Water Level",
}

export default function SensorReadings() {
    const user = useContext(userContext)
    const [sensors, setSensors] = useState<Sensor[]>([])
    const [readings, setReadings] = useState<SensorReading[]>([])
    const [error, setError] = useState("")
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        let cancelled = false
        const load = async () => {
            if (!user.accessToken) return
            const [sensorResult, readingResult] = await Promise.all([
                getSensors(user.accessToken),
                getSensorReadings(user.accessToken),
            ])
            if (cancelled) return
            if (!sensorResult.success || !readingResult.success) {
                setError(sensorResult.msg || readingResult.msg)
            } else {
                setSensors(sensorResult.data || [])
                setReadings(readingResult.data || [])
                setError("")
            }
            setLoading(false)
        }
        load()
        const timer = window.setInterval(load, 10_000)
        return () => { cancelled = true; window.clearInterval(timer) }
    }, [user.accessToken])

    const latestBySensor = useMemo(() => {
        const map = new Map<number, SensorReading>()
        for (const reading of readings) {
            const current = map.get(reading.sensor)
            if (!current || new Date(reading.timestamp).getTime() > new Date(current.timestamp).getTime()) {
                map.set(reading.sensor, reading)
            }
        }
        return map
    }, [readings])

    return (
        <Panel styles="p-3 px-4 flex flex-col gap-4">
            <IconTitle title="Live Sensors" icon={<MdSensors />} />
            {loading && <p className="text-sm text-subtext2">Loading sensor telemetry…</p>}
            {error && <p className="text-sm text-high">Sensor API: {error}</p>}
            {!loading && !error && sensors.length === 0 && <p className="text-sm text-subtext2">No sensors configured.</p>}
            <div className="grid grid-cols-2 gap-2">
                {sensors.map(sensor => {
                    const reading = latestBySensor.get(sensor.id)
                    return (
                        <InformationPanel
                            key={sensor.id}
                            name={labels[sensor.sensor_type] || sensor.sensor_type}
                            value={reading ? `${Number(reading.value).toFixed(2)} ${sensor.unit}` : "Waiting…"}
                        />
                    )
                })}
            </div>
        </Panel>
    )
}
