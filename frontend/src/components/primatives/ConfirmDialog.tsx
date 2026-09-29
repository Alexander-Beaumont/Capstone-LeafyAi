import Button from "./Button"
import Modal from "./Modal"

interface Props {
    open: boolean
    title: string
    text: string
    confirm: string
    busy?: boolean
    onConfirm: () => void
    onClose: () => void
}

export default function ConfirmDialog({ open, title, text, confirm, busy, onConfirm, onClose }: Props) {
    return (
        <Modal open={open} onClose={() => { if (!busy) onClose() }}>
            <div className="bg-panel1 border border-border p-5 flex flex-col rounded-xl w-[80%] max-w-xl gap-3">
                <p className="text-xl font-semibold text-title">{title}</p>
                <p className="text-sm text-subtext1">{text}</p>
                <div className="flex gap-3">
                    <Button name={confirm} highlight loading={busy} onSubmit={onConfirm} />
                    <Button name="Cancel" highlight={false} onSubmit={() => { if (!busy) onClose() }} />
                </div>
            </div>
        </Modal>
    )
}
