import { useContext } from "react"
import InformationPanel from "../primatives/InformationPanel"
import { FarmOverviewContext } from "../../providers/FarmOverviewProvider"
import { findSensor, formatReading, statusHint } from "../../util/sensor-readings"

export default function SensorReadings() {
    const overview = useContext(FarmOverviewContext)
    const sensors = overview.farmState?.devices[0]?.sensors ?? []
    const showSkeleton = overview.loading && !overview.farmState

    const temperature = findSensor(sensors, "ambient_temperature")
    const humidity = findSensor(sensors, "relative_humidity")
    const ph = findSensor(sensors, "water_ph")
    const ec = findSensor(sensors, "electrical_conductivity")
    const waterLevel = findSensor(sensors, "reservoir_water_level")

    const cards = [
        { name: "Temperature", value: formatReading(temperature, "°C"), hint: statusHint(temperature), muted: !temperature || temperature.status !== "fresh" },
        { name: "Humidity", value: formatReading(humidity, "%"), hint: statusHint(humidity), muted: !humidity || humidity.status !== "fresh" },
        { name: "pH", value: formatReading(ph, ""), hint: statusHint(ph), muted: !ph || ph.status !== "fresh" },
        { name: "EC", value: formatReading(ec), hint: statusHint(ec), muted: !ec || ec.status !== "fresh" },
        { name: "Water Level", value: formatReading(waterLevel, "cm"), hint: statusHint(waterLevel), muted: !waterLevel || waterLevel.status !== "fresh" },
    ]

    return (
        <div className="grid grid-cols-2 gap-2 [&>*:last-child:nth-child(odd)]:col-span-2">
            {cards.map(card => (
                <InformationPanel
                    key={card.name}
                    name={card.name}
                    value={card.value}
                    hint={card.hint}
                    muted={card.muted}
                    loading={showSkeleton}
                />
            ))}
        </div>
    )
}
