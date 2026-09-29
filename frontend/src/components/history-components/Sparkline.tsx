interface Props {
    values: number[]
}

export default function Sparkline({ values }: Props) {
    if (values.length === 0) return null
    const width = 280
    const height = 64
    const min = Math.min(...values)
    const max = Math.max(...values)
    const span = max - min || 1
    const points = values.map((value, index) => {
        const x = values.length === 1 ? width / 2 : (index / (values.length - 1)) * width
        const y = height - ((value - min) / span) * (height - 8) - 4
        return `${x},${y}`
    }).join(" ")

    return (
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-16 text-highlight" role="img">
            <polyline fill="none" stroke="currentColor" strokeWidth="2" points={points} />
        </svg>
    )
}
