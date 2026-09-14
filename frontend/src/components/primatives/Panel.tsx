import type { ReactNode } from "react"

interface PanelProps{
    styles?: string
    children: ReactNode
}

export default function Panel({styles, children}: PanelProps) {
    return (
        <div className={`border border-border bg-panel1 rounded-lg ${styles}`}>
            {children}
        </div>
    )
}
