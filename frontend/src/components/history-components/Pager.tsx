import Button from "../primatives/Button"

interface Props {
    offset: number
    limit: number
    count: number
    onOffset: (offset: number) => void
}

export default function Pager({ offset, limit, count, onOffset }: Props) {
    const page = Math.floor(offset / limit) + 1
    const pages = Math.max(1, Math.ceil(count / limit))
    return (
        <div className="flex items-center justify-between gap-3">
            <p className="text-xs text-subtext3">{count} results</p>
            <div className="flex items-center gap-2">
                <Button
                    name="Previous"
                    highlight={false}
                    onSubmit={() => {
                        if (offset > 0) onOffset(Math.max(0, offset - limit))
                    }}
                />
                <p className="text-xs text-subtext2">{page} / {pages}</p>
                <Button
                    name="Next"
                    highlight={false}
                    onSubmit={() => {
                        if (offset + limit < count) onOffset(offset + limit)
                    }}
                />
            </div>
        </div>
    )
}
