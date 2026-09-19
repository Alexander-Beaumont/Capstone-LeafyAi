import Panel from "./Panel"
import { FiRefreshCw } from "react-icons/fi";

interface Props{
    title: string
    icon: React.ReactNode
    refresh?: boolean
    onRefresh?: () => void
    refreshLabel?: string
    refreshing?: boolean
}

export default function PageTitlePanel({title, icon, refresh, onRefresh, refreshLabel, refreshing}: Props) {
    return (
        <Panel styles="w-full p-3 flex items-center justify-between">
            <div className="flex gap-3">
                <div className="bg-panel2 border text-xl flex items-center w-9 justify-center border-border p-1 rounded-md text-subtext1">
                    {icon}
                </div>
                <p className="text-3xl font-semibold text-title flex  items-center gap-1.5">
                    {title}
                </p>
            </div>
            {refresh || refreshLabel ?
                <div className="flex items-center gap-3 mr-1">
                    {refreshLabel ?
                        <p className="text-subtext3 text-xs">
                            {refreshLabel}
                        </p>
                    : null}
                    {refresh ?
                        <button
                            type="button"
                            aria-label="Refresh"
                            disabled={refreshing}
                            onClick={onRefresh}
                            className={`text-md font-bold text-subtext2 bg-transparent border-0 p-0 ${refreshing ? "opacity-60 cursor-not-allowed" : "hover:cursor-pointer"}`}
                        >
                            <FiRefreshCw
                                className={`${refreshing ? "animate-spin" : "active:rotate-360"} transition-all duration-500`}
                            />
                        </button>
                    : null}
                </div>
            : null}
        </Panel>
    )
}
