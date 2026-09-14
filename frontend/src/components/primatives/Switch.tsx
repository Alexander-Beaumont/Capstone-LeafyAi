interface TickeProps{
    ticked: boolean | undefined
    setTicked: (ticked: boolean) => void
}
export default function Switch(props: TickeProps) {

    function tick() {
        props.setTicked(!props.ticked)
    }

    return (
        <div
        className={`shadow-[inset_0_2px_4px_rgba(0,0,0,0.15)] dark:shadow-none w-9.5  rounded-full  flex items-center p-0.5  cursor-pointer ${props.ticked ? "bg-highlight" : "bg-progress-panel lh-5"} duration-200 ease-in-out`}
        onClick={() => {
            tick()
        }}
        >
        <div
            className={`h-4 w-4 rounded-full duration-200 ease-in-out transform ${props.ticked ? "translate-x-4.5 dark:bg-panel1 bg-subtext1" : "translate-x-0 bg-subtext2"}`}
        ></div>
        </div>
    );
}