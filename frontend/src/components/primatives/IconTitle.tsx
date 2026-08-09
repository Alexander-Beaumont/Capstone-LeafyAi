import type React from "react"

interface Props{
    title: string,
    icon: React.ReactNode
}

export default function IconTitle({title, icon}: Props) {
    return (
        <div className="flex items-center gap-2">
            <div className="bg-panel2 border border-border p-1 rounded-md text-subtext1">
                {icon}
            </div>
            <p className="text-md font-semibold text-title flex  items-center gap-1.5">
                {title}
            </p>
        </div>
    )
}
