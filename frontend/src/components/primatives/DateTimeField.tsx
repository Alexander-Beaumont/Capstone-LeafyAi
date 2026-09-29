import { useEffect, useRef, useState } from "react"

interface Props {
    name: string
    value: string
    setValue: (value: string) => void
}

const WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

function pad(value: number) {
    return String(value).padStart(2, "0")
}

function toLocalValue(date: Date) {
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function parseLocal(value: string) {
    const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(value)
    if (!match) return null
    const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]), Number(match[4]), Number(match[5]))
    return Number.isNaN(date.getTime()) ? null : date
}

function displayValue(value: string) {
    const date = parseLocal(value)
    if (!date) return "Choose date"
    return `${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export default function DateTimeField({ name, value, setValue }: Props) {
    const selected = parseLocal(value)
    const [open, setOpen] = useState(false)
    const [cursor, setCursor] = useState(() => selected ?? new Date())
    const [hourText, setHourText] = useState(selected ? pad(selected.getHours()) : "")
    const [minuteText, setMinuteText] = useState(selected ? pad(selected.getMinutes()) : "")
    const root = useRef<HTMLDivElement>(null)

    useEffect(() => {
        if (!open) return
        function close(event: MouseEvent) {
            if (!root.current?.contains(event.target as Node)) setOpen(false)
        }
        document.addEventListener("mousedown", close)
        return () => document.removeEventListener("mousedown", close)
    }, [open])

    function commitClock(nextHour: string, nextMinute: string) {
        const hours = Math.min(23, Math.max(0, Number(nextHour) || 0))
        const minutes = Math.min(59, Math.max(0, Number(nextMinute) || 0))
        const base = selected ?? new Date(cursor.getFullYear(), cursor.getMonth(), Math.min(cursor.getDate(), new Date(cursor.getFullYear(), cursor.getMonth() + 1, 0).getDate()), 0, 0)
        setHourText(pad(hours))
        setMinuteText(pad(minutes))
        setValue(toLocalValue(new Date(base.getFullYear(), base.getMonth(), base.getDate(), hours, minutes)))
    }

    function chooseDay(day: number) {
        const hours = Math.min(23, Math.max(0, Number(hourText) || 0))
        const minutes = Math.min(59, Math.max(0, Number(minuteText) || 0))
        setHourText(pad(hours))
        setMinuteText(pad(minutes))
        setValue(toLocalValue(new Date(cursor.getFullYear(), cursor.getMonth(), day, hours, minutes)))
    }

    const year = cursor.getFullYear()
    const month = cursor.getMonth()
    const firstWeekday = (new Date(year, month, 1).getDay() + 6) % 7
    const days = new Date(year, month + 1, 0).getDate()
    const cells = [...Array(firstWeekday).fill(null), ...Array.from({ length: days }, (_, index) => index + 1)]

    return (
        <div ref={root} className="relative flex flex-col gap-1.5">
            <p className="text-xs font-medium text-subtext1">{name}</p>
            <button
                type="button"
                className="h-7 rounded-md bg-panel2 outline-1 outline-border2 px-2 text-left text-xs text-subtext1 hover:cursor-pointer"
                onClick={() => {
                    setCursor(selected ?? new Date())
                    setOpen(current => !current)
                }}
            >
                {displayValue(value)}
            </button>
            {open ?
                <div className="absolute top-full left-0 z-30 mt-1 w-72 rounded-lg border border-border bg-panel1 p-3 flex flex-col gap-3">
                    <div className="flex items-center justify-between">
                        <button type="button" className="h-7 px-2 rounded-md text-sm text-subtext1 hover:bg-panel3 hover:cursor-pointer" onClick={() => setCursor(new Date(year, month - 1, 1))}>Prev</button>
                        <p className="text-sm text-title font-semibold">{MONTHS[month]} {year}</p>
                        <button type="button" className="h-7 px-2 rounded-md text-sm text-subtext1 hover:bg-panel3 hover:cursor-pointer" onClick={() => setCursor(new Date(year, month + 1, 1))}>Next</button>
                    </div>
                    <div className="grid grid-cols-7 gap-1 text-center">
                        {WEEKDAYS.map(day => <p key={day} className="text-[10px] text-subtext3">{day}</p>)}
                        {cells.map((day, index) => day == null ?
                            <span key={`empty-${index}`} />
                        :
                            <button
                                key={day}
                                type="button"
                                className={`h-7 rounded-md text-xs hover:cursor-pointer ${selected && selected.getFullYear() === year && selected.getMonth() === month && selected.getDate() === day ? "bg-highlight text-btn-text" : "text-subtext1 hover:bg-panel3"}`}
                                onClick={() => chooseDay(day)}
                            >
                                {day}
                            </button>
                        )}
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                        <label className="flex flex-col gap-1 text-xs text-subtext1">
                            Hour
                            <input
                                className="h-7 rounded-md bg-panel2 outline-1 outline-border2 px-2 text-xs text-subtext1"
                                inputMode="numeric"
                                value={hourText}
                                placeholder="00"
                                onChange={event => setHourText(event.target.value.replace(/\D/g, "").slice(0, 2))}
                                onBlur={() => commitClock(hourText, minuteText)}
                            />
                        </label>
                        <label className="flex flex-col gap-1 text-xs text-subtext1">
                            Minute
                            <input
                                className="h-7 rounded-md bg-panel2 outline-1 outline-border2 px-2 text-xs text-subtext1"
                                inputMode="numeric"
                                value={minuteText}
                                placeholder="00"
                                onChange={event => setMinuteText(event.target.value.replace(/\D/g, "").slice(0, 2))}
                                onBlur={() => commitClock(hourText, minuteText)}
                            />
                        </label>
                    </div>
                    <button type="button" className="h-7 rounded-md text-xs text-subtext3 hover:bg-panel3 hover:cursor-pointer" onClick={() => { setHourText(""); setMinuteText(""); setValue("") }}>Clear</button>
                </div>
            : null}
        </div>
    )
}
