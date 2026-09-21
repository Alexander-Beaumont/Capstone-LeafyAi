import type {
    AIConfiguration,
    AIDecision,
    FarmAction,
    RecommendationRun,
} from "./types"

export function parseConfidence(score: string | number | null | undefined): number | null {
    if (score == null || score === "") return null
    const value = typeof score === "number" ? score : Number(score)
    return Number.isFinite(value) ? value : null
}

export function isValidTimeZone(value: string): boolean {
    if (!value.trim()) return false
    try {
        Intl.DateTimeFormat("en", { timeZone: value.trim() })
        return true
    } catch {
        return false
    }
}

export function toApiTime(value: string): string {
    if (/^\d{2}:\d{2}$/.test(value)) return `${value}:00`
    return value
}

export function toInputTime(value: string): string {
    return value.slice(0, 5)
}

export function isValidClock(value: string): boolean {
    const match = /^(\d{2}):(\d{2})$/.exec(value.trim())
    if (!match) return false
    const hour = Number(match[1])
    const minute = Number(match[2])
    return hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59
}

export function validateAiSettings(form: {
    scheduleEnabled: boolean
    intervalMinutes: string
    maxImages: string
    activeStartTime: string
    activeEndTime: string
}) {
    const errors: Record<string, string> = {}
    if (!form.scheduleEnabled) return errors
    const interval = Number(form.intervalMinutes)
    if (!Number.isInteger(interval) || interval < 1 || interval > 1440) {
        errors.intervalMinutes = "Interval must be between 1 and 1440 minutes."
    }
    const maxImages = Number(form.maxImages)
    if (!Number.isInteger(maxImages) || maxImages < 1 || maxImages > 8) {
        errors.maxImages = "Image limit must be between 1 and 8."
    }
    if (!isValidClock(form.activeStartTime)) {
        errors.activeStartTime = "Start time must be 24-hour HH:MM."
    }
    if (!isValidClock(form.activeEndTime)) {
        errors.activeEndTime = "End time must be 24-hour HH:MM."
    } else if (!errors.activeStartTime && toApiTime(form.activeStartTime) === toApiTime(form.activeEndTime)) {
        errors.activeEndTime = "Start and end times must differ."
    }
    return errors
}

function zonedParts(date: Date, timeZone: string) {
    const parts = new Intl.DateTimeFormat("en-US", {
        timeZone,
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hourCycle: "h23",
    }).formatToParts(date)
    const get = (type: string) => Number(parts.find(part => part.type === type)?.value)
    return {
        year: get("year"),
        month: get("month"),
        day: get("day"),
        hour: get("hour"),
        minute: get("minute"),
        second: get("second"),
    }
}

function zonedDate(timeZone: string, year: number, month: number, day: number, hour: number, minute: number, second = 0) {
    const utcGuess = Date.UTC(year, month - 1, day, hour, minute, second)
    const asZone = zonedParts(new Date(utcGuess), timeZone)
    const asIfLocal = Date.UTC(asZone.year, asZone.month - 1, asZone.day, asZone.hour, asZone.minute, asZone.second)
    return new Date(utcGuess - (asIfLocal - utcGuess))
}

function addDays(year: number, month: number, day: number, amount: number) {
    const utc = new Date(Date.UTC(year, month - 1, day + amount))
    return { year: utc.getUTCFullYear(), month: utc.getUTCMonth() + 1, day: utc.getUTCDate() }
}

function parseClock(value: string) {
    const [hour, minute, second = "0"] = value.split(":")
    return { hour: Number(hour), minute: Number(minute), second: Number(second) || 0 }
}

function clockMinutes(value: { hour: number; minute: number; second: number }) {
    return value.hour * 60 + value.minute + value.second / 60
}

export function nextScheduleTime(settings: AIConfiguration | null, now = new Date()): Date | null {
    if (!settings?.schedule_enabled || !isValidTimeZone(settings.timezone)) return null
    const start = parseClock(settings.active_start_time)
    const end = parseClock(settings.active_end_time)
    const interval = Math.max(1, settings.interval_minutes)
    const local = zonedParts(now, settings.timezone)
    const currentMinutes = clockMinutes(local)
    const startMinutes = clockMinutes(start)
    const endMinutes = clockMinutes(end)
    const sameDayWindow = startMinutes < endMinutes

    const atStartOn = (date: { year: number; month: number; day: number }, extraMinutes = 0) => {
        const total = startMinutes + extraMinutes
        const dayShift = Math.floor(total / (24 * 60))
        const remainder = ((total % (24 * 60)) + 24 * 60) % (24 * 60)
        const shifted = addDays(date.year, date.month, date.day, dayShift)
        return zonedDate(
            settings.timezone,
            shifted.year,
            shifted.month,
            shifted.day,
            Math.floor(remainder / 60),
            Math.floor(remainder % 60),
            0,
        )
    }

    const today = { year: local.year, month: local.month, day: local.day }
    const tomorrow = addDays(today.year, today.month, today.day, 1)
    const yesterday = addDays(today.year, today.month, today.day, -1)

    const nextInWindow = (windowStartDate: { year: number; month: number; day: number }, elapsedMinutes: number, windowEnd: Date) => {
        const nextOffset = (Math.floor(elapsedMinutes / interval) + 1) * interval
        const candidate = atStartOn(windowStartDate, nextOffset)
        return candidate < windowEnd ? candidate : null
    }

    if (sameDayWindow) {
        const windowEnd = zonedDate(settings.timezone, today.year, today.month, today.day, end.hour, end.minute, end.second)
        if (currentMinutes < startMinutes) return atStartOn(today)
        if (currentMinutes < endMinutes) {
            return nextInWindow(today, currentMinutes - startMinutes, windowEnd) ?? atStartOn(tomorrow)
        }
        return atStartOn(tomorrow)
    }

    if (currentMinutes >= startMinutes) {
        const windowEnd = zonedDate(settings.timezone, tomorrow.year, tomorrow.month, tomorrow.day, end.hour, end.minute, end.second)
        return nextInWindow(today, currentMinutes - startMinutes, windowEnd) ?? atStartOn(tomorrow)
    }
    if (currentMinutes < endMinutes) {
        const windowEnd = zonedDate(settings.timezone, today.year, today.month, today.day, end.hour, end.minute, end.second)
        return nextInWindow(yesterday, currentMinutes + (24 * 60 - startMinutes), windowEnd) ?? atStartOn(today)
    }
    return atStartOn(today)
}

export function formatInTimeZone(date: Date, timeZone: string) {
    return new Intl.DateTimeFormat("en-AU", {
        timeZone,
        dateStyle: "medium",
        timeStyle: "short",
    }).format(date)
}

export function isAutomated(decision: AIDecision) {
    return decision.execution_type === "automated"
}

export function isAdvisory(decision: AIDecision) {
    return !isAutomated(decision)
}

export function isSafetyBlocked(decision: AIDecision) {
    return decision.safety_check?.result === "failed"
}

export function isNoOpAction(action: FarmAction) {
    return Boolean(action.previous_state) && action.previous_state === action.confirmed_state && action.result === "success"
}

export function recommendationBadges(decision: AIDecision) {
    const badges: string[] = []
    if (isAutomated(decision)) badges.push("Automatic")
    else badges.push("Advisory")
    if (isSafetyBlocked(decision)) badges.push("Safety blocked")
    const actions = decision.actions ?? []
    if (actions.length === 0) {
        if (isAdvisory(decision) || isSafetyBlocked(decision)) badges.push("No action")
        return badges
    }
    for (const action of actions) {
        if (isNoOpAction(action)) badges.push("No-op")
        else if (action.result === "success") badges.push("Executed")
        else if (action.result === "failed") badges.push("Hardware failed")
        else if (action.result === "partial") badges.push("Partial")
    }
    return badges
}

export function actionSummary(run: RecommendationRun | null) {
    if (!run) return "No run"
    const actions = run.recommendations.flatMap(item => item.actions ?? [])
    const executed = actions.filter(action => action.result === "success" && !isNoOpAction(action)).length
    const noOps = actions.filter(isNoOpAction).length
    const failed = actions.filter(action => action.result === "failed").length
    const advisory = run.recommendations.filter(isAdvisory).length
    const blocked = run.recommendations.filter(isSafetyBlocked).length
    return `${executed} executed, ${noOps} no-op, ${failed} failed, ${advisory} advisory, ${blocked} blocked`
}

export function qualityTone(status: string): "ok" | "warn" | "bad" | "default" {
    if (status === "PASS") return "ok"
    if (status === "WARN") return "warn"
    if (status === "FAIL") return "bad"
    return "default"
}

export function inputModeLabel(mode: RecommendationRun["input_mode"] | undefined, fallbackUsed = false) {
    if (mode === "vlm") return "VLM"
    if (mode === "llm") return fallbackUsed ? "LLM fallback" : "LLM"
    return "None"
}
