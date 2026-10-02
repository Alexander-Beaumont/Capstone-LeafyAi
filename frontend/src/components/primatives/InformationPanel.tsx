import { Link } from 'react-router'
import Panel from './Panel'

interface Props{
    name: string
    value: string
    hint?: string
    note?: string
    muted?: boolean
    loading?: boolean
    to?: string
    compact?: boolean
}
export default function InformationPanel({name, value, hint, note, muted, loading, to, compact}: Props) {
    const panel = (
        <Panel styles={`${compact ? "p-2 gap-1" : "p-3 gap-2"} flex flex-col flex-1 w-full h-full ${to ? "hover:border-highlight" : ""}`}>
            <p className={`text-subtext2 ${compact ? "text-xs" : "text-sm"}`}>
                {name}
            </p>
            {loading ?
                <div className={`${compact ? "h-5 w-12" : "h-8 w-16"} bg-panel2 animate-pulse rounded-md`} />
            :
                <p className={`${muted ? "text-subtext2" : "text-highlight"} ${compact ? "text-lg" : "text-3xl"}`}>
                    {value}
                </p>
            }
            {hint && !loading ?
                <p className="text-subtext3 text-xs">
                    {hint}
                </p>
            : null}
            {note && !loading ?
                <p className="text-subtext3 text-xs">
                    {note}
                </p>
            : null}
        </Panel>
    )
    if (!to) return panel
    return (
        <Link to={to} className="flex min-w-fit flex-1 flex-col hover:cursor-pointer">
            {panel}
        </Link>
    )
}
