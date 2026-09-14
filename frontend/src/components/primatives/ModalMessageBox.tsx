import Button from "./Button"

interface Props{
    title: string
    text: string
    onClose: () => void
}
export default function ModalMessageBox({title, text, onClose}: Props) {
    return (
        <div className="bg-panel1 border border-border p-5 flex flex-col items-center
            rounded-xl w-[80%] max-w-80 gap-3
        ">
            <p className="text-xl font-semibold text-title">
                {title}
            </p>
            <p className="text-subtext1 mb-1.5 text-center">
                {text}
            </p>
            <Button
                name="Close"
                highlight={true}
                styles={{fullWidth: false, noAnimation: true}}
                onSubmit={() => onClose()}
            />
        </div>
    )
}
