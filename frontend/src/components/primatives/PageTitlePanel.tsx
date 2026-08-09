import Panel from "./Panel"

interface Props{
    title: string,
    icon: React.ReactNode
}

export default function PageTitlePanel({title, icon}: Props) {
    return (
        <Panel styles="w-full p-3 flex gap-3">
            <div className="bg-panel2 border text-xl flex items-center w-9 justify-center border-border p-1 rounded-md text-subtext1">
                {icon}
            </div>
            <p className="text-3xl font-semibold text-title flex  items-center gap-1.5">
                {title}
            </p>
        </Panel>
    )
}
