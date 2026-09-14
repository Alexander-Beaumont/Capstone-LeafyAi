import Panel from "./Panel"
import { FiRefreshCw } from "react-icons/fi";

interface Props{
    title: string,
    icon: React.ReactNode
    refresh?: boolean
}

export default function PageTitlePanel({title, icon, refresh}: Props) {
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
            {!refresh ? "" : 
                <FiRefreshCw className="text-md font-bold text-subtext2 mr-1 hover:cursor-pointer active:rotate-360
                transition-all duration-500"/>
            }
        </Panel>
    )
}
