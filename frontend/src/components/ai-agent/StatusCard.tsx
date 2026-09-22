interface Props {
    name: string
    value: string
    hint?: string
    loading?: boolean
}

export default function StatusCard({ name, value, hint, loading }: Props) {
    return (
        <div className="border border-border bg-panel1 rounded-lg p-3 flex flex-col gap-2 min-w-0">
            <p className="text-subtext2 text-sm">{name}</p>
            {loading ?
                <div className="h-8 w-16 bg-panel2 animate-pulse rounded-md" />
            :
                <p className="text-highlight text-xl font-semibold break-words">{value}</p>
            }
            {hint && !loading ?
                <p className="text-subtext3 text-xs break-words">{hint}</p>
            : null}
        </div>
    )
}
