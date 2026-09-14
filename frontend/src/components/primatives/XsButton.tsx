import type { ReactNode } from "react"


interface Props{
    highlight: boolean,
    name: string | ReactNode,
    onClick: () => void,
    animate?: boolean
}
export default function XsButton({highlight, name, onClick, animate}: Props) {
    return (
        <button className={`border hover:cursor-pointer hover:rounded-lg hover:italic transition-all ${animate ? "duration-200" : "duration-0"}
             ${highlight ? "border-highlight text-highlight" : "border-border2 text-subtext2"} rounded-md text-xs px-2 p-1 text-center bg-panel3`}
             onClick={() => onClick()}>
            {name}
        </button>
    )
}
