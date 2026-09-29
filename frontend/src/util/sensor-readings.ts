import type { FarmSensorState } from "./types"

const SENSOR_NAMES: Record<string, string> = {
    ambient_temperature: "Temperature",
    relative_humidity: "Humidity",
    water_ph: "pH",
    electrical_conductivity: "EC",
    reservoir_water_level: "Water Level",
    water_temperature: "Water temperature",
    dew_point: "Dew point",
}

export function sensorLabel(slug: string) {
    return SENSOR_NAMES[slug] ?? slug.replaceAll("_", " ")
}

export function findSensor(sensors: FarmSensorState[], slug: string) {
    return sensors.find(sensor => sensor.sensor_slug === slug)
}

function formatNumber(value: number) {
    return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

export function formatReading(sensor: FarmSensorState | undefined, unitOverride?: string) {
    if (!sensor || sensor.value == null) return "—"
    const unit = unitOverride ?? sensor.unit
    const amount = formatNumber(sensor.value)
    if (!unit) return amount
    if (unit === "%" || unit.startsWith("°")) return `${amount}${unit}`
    return `${amount} ${unit}`
}

function formatAge(ageSeconds: number | null) {
    if (ageSeconds == null) return ""
    if (ageSeconds < 60) return `${ageSeconds}s ago`
    const minutes = Math.round(ageSeconds / 60)
    if (minutes < 60) return `${minutes}m ago`
    return `${Math.round(minutes / 60)}h ago`
}

export function statusHint(sensor: FarmSensorState | undefined) {
    if (!sensor || sensor.status === "missing") return "missing"
    const age = formatAge(sensor.age_seconds)
    if (sensor.status === "stale") return age ? `stale ${age}` : "stale"
    if (sensor.quality_status === "suspect") return sensor.quality_notes || "suspect"
    return age
}
