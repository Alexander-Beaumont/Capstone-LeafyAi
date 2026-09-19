import Panel from './Panel'

interface Props{
    name: string
    value: string
    hint?: string
    muted?: boolean
    loading?: boolean
}
export default function InformationPanel({name, value, hint, muted, loading}: Props) {
    return (
        <Panel styles='p-3 flex flex-col gap-2 min-w-fit flex-1'>
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
        </Panel>
    )
}
