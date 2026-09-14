import type { ReactNode } from "react"
import type { ButtonStyles } from "../../util/types"
import { VscLoadingCompact } from "react-icons/vsc";

interface Props{
    name: string | ReactNode
    onSubmit: () => Promise<void> | void
    icon?: ReactNode
    highlight: boolean
    loading?: boolean
    styles?: ButtonStyles
}
export default function Button({name, onSubmit, icon, highlight: highligh, styles: s, loading}: Props) {
    return (
        <button className={` shadow-gray-200 dark:shadow-none flex justify-center items-center 
            ${highligh ? `bg-highlight 
                ${s?.noAnimation ? "" : "hover:bg-highlight/93 hover:rounded-lg"} text-btn-text` : 
            `outline-1  outline-border2   text-subtext3 bg-panel2 
            ${s?.noAnimation ? "" : "hover:bg-panel3 hover:rounded-lg"}`} 
            ${s?.noAnimation ? "" : "transition-all duration-250 ease-in-out"} text-sm  h-8
            px-5 font-medium rounded-md  hover:cursor-pointer ${s?.fullWidth ? "w-full" : ""} flex gap-1
            ${loading ? "disabled:opacity-80 disabled:cursor-not-allowed" : ""}`}
            onClick={async () => {
                onSubmit()
            }}
            disabled={loading}>
            {loading ? (
                    <VscLoadingCompact className="animate-spin" />
                ) : (
                    <>
                        {!s?.rightSide && icon}
                        {name}
                        {s?.rightSide && icon}
                    </>
                )}
        </button>
    )
}