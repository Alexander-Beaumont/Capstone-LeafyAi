import type { ReactNode } from "react"

type BadgeTone = "default" | "ok" | "warn" | "bad"

const TONES: Record<BadgeTone, string> = {
    default: "border-border text-subtext1 bg-panel3",
    ok: "border-low text-low bg-panel3",
    warn: "border-medium text-medium bg-panel3",
    bad: "border-high text-high bg-panel3",
}

interface Props {
    label: ReactNode
    tone?: BadgeTone
}

export default function Badge({ label, tone = "default" }: Props) {
    return (
        <span className={`border rounded-full text-xs px-2 h-5 inline-flex items-center whitespace-nowrap ${TONES[tone]}`}>
            {label}
        </span>
    )
}
