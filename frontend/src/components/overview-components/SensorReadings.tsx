import InformationPanel from "../primatives/InformationPanel"

export default function SensorReadings() {
    return (
        <div className="grid grid-cols-2 gap-2 ">
            <InformationPanel
                name="Temperature"
                value="24c"
            />
            <InformationPanel
                name="Humidity"
                value="64%"
            />
            <InformationPanel
                name="pH"
                value="6.1"
            />
            <InformationPanel
                name="EC"
                value="1.3"
            />
            <InformationPanel
                name="Water Level"
                value="72%"
            />
            <InformationPanel
                name="FLow (L/min)"
                value="22"
            />
        </div>
    )
}
