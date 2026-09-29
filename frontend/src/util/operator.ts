import { Util } from "./Util"

export function formatTimestamp(value: string | null | undefined) {
    if (!value) return "None"
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return Util.formatDateTime(date)
}

export function ingestionLabel(status: string | undefined) {
    if (status === "healthy") return "Healthy"
    if (status === "error") return "Error"
    if (status === "disabled") return "Off"
    if (status === "not_configured") return "None"
    return "…"
}

export function localInputToIso(value: string) {
    if (!value) return undefined
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return undefined
    return date.toISOString()
}

export function readingNumber(value: string | number | null | undefined) {
    if (value == null || value === "") return null
    const parsed = typeof value === "number" ? value : Number(value)
    return Number.isFinite(parsed) ? parsed : null
}
