
import { LuHouse } from "react-icons/lu";
import SensorReadings from "../components/overview-components/SensorReadings";
import DeviceControls from "../components/overview-components/DeviceControls";
import AwaitingDecisions from "../components/overview-components/AwaitingDecisions";
import PageTitlePanel from "../components/primatives/PageTitlePanel";

export default function FarmOverview() {

    return (
        <div className="flex flex-col w-full items-center p-5 max-w-250 m-auto gap-5">
            <PageTitlePanel
                title="Farm Overview"
                icon={ <LuHouse />}
            />
            <div className="grid grid-cols-[minmax(0,auto)_minmax(0,1fr)] gap-5 w-full">
                <SensorReadings/>
               <DeviceControls/>
            </div>
           <AwaitingDecisions/>
        </div>
    )
}
