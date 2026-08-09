import PageTitlePanel from "../components/primatives/PageTitlePanel";
import { PiPlant } from "react-icons/pi";

export default function PlantVision() {
    return (
        <div className="flex flex-col w-full items-center p-5 max-w-250 m-auto gap-5">
            <PageTitlePanel
                title="Plant Vision"
                icon={  <PiPlant />}
            />
        </div>
    )
}
