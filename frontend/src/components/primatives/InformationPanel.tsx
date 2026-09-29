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
}
export default function InformationPanel({name, value, hint, note, muted, loading, to}: Props) {
    const panel = (
        <Panel styles={`p-3 flex flex-col gap-2 min-w-fit flex-1 w-full h-full ${to ? "hover:border-highlight" : ""}`}>
            <p className='text-subtext2 text-sm'>
                {name}
            </p>
            {loading ?
                <div className="h-8 w-16 bg-panel2 animate-pulse rounded-md" />
            :
                <p className={`${muted ? "text-subtext2" : "text-highlight"} text-3xl`}>
                    {value}
                </p>
            }
            {hint && !loading ?
                <p className='text-subtext3 text-xs'>
                    {hint}
                </p>
            : null}
            {note && !loading ?
                <p className='text-subtext3 text-xs'>
                    {note}
                </p>
            : null}
        </Panel>
    )
    if (!to) return panel
    return (
        <Link to={to} className="block min-w-0 hover:cursor-pointer">
            {panel}
        </Link>
    )
}
