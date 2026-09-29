import type { SensorHistoryPoint } from "../../util/types"

interface Props {
    points: SensorHistoryPoint[]
    unit: string
}

function pad(value: number) {
    return String(value).padStart(2, "0")
}

function labelTime(value: string) {
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return `${pad(date.getDate())}/${pad(date.getMonth() + 1)} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export default function Sparkline({ points, unit }: Props) {
    const samples = points
        .map(point => ({ ...point, time: new Date(point.timestamp).getTime() }))
        .filter(point => Number.isFinite(point.time) && Number.isFinite(point.average))
    if (samples.length === 0) return null

    const width = 640
    const height = 180
    const padLeft = 8
    const padRight = 8
    const padTop = 12
    const padBottom = 12
    const lows = samples.map(point => point.minimum)
    const highs = samples.map(point => point.maximum)
    const min = Math.min(...lows, ...samples.map(point => point.average))
    const max = Math.max(...highs, ...samples.map(point => point.average))
    const span = max - min || 1
    const start = samples[0].time
    const end = samples[samples.length - 1].time
    const timeSpan = end - start || 1

    function x(time: number) {
        if (samples.length === 1) return width / 2
        return padLeft + ((time - start) / timeSpan) * (width - padLeft - padRight)
    }
    function y(value: number) {
        return padTop + (1 - (value - min) / span) * (height - padTop - padBottom)
    }

    const average = samples.map(point => `${x(point.time)},${y(point.average)}`).join(" ")
    const band = [
        ...samples.map(point => `${x(point.time)},${y(point.maximum)}`),
        ...samples.slice().reverse().map(point => `${x(point.time)},${y(point.minimum)}`),
    ].join(" ")

    return (
        <div className="flex flex-col gap-1">
            <div className="flex justify-between text-[10px] text-subtext3">
                <span>{max} {unit}</span>
                <span>{min} {unit}</span>
            </div>
            <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-44 text-highlight" role="img">
                <polygon points={band} fill="currentColor" opacity="0.15" />
                <polyline fill="none" stroke="currentColor" strokeWidth="2" points={average} />
                {samples.length === 1 ?
                    <circle cx={x(samples[0].time)} cy={y(samples[0].average)} r="3" fill="currentColor" />
                : null}
            </svg>
            <div className="flex justify-between text-[10px] text-subtext3">
                <span>{labelTime(samples[0].timestamp)}</span>
                <span>{labelTime(samples[samples.length - 1].timestamp)}</span>
            </div>
        </div>
    )
}
