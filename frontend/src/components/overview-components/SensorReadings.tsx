import { useContext } from "react"
import InformationPanel from "../primatives/InformationPanel"
import { FarmOverviewContext } from "../../providers/FarmOverviewProvider"
import { findSensor, formatReading, statusHint } from "../../util/sensor-readings"
import { PAGES } from "../../util/constants"

export default function SensorReadings() {
    const overview = useContext(FarmOverviewContext)
    const sensors = overview.farmState?.devices[0]?.sensors ?? []
    const showSkeleton = overview.loading && !overview.farmState

    const temperature = findSensor(sensors, "ambient_temperature")
    const humidity = findSensor(sensors, "relative_humidity")
    const ph = findSensor(sensors, "water_ph")
    const ec = findSensor(sensors, "electrical_conductivity")
    const waterLevel = findSensor(sensors, "reservoir_water_level")

    const history = PAGES.authPages.history
    const cards = [
        { name: "Temperature", slug: "ambient_temperature", value: formatReading(temperature, "°C"), hint: statusHint(temperature), muted: !temperature || temperature.status !== "fresh" },
        { name: "Humidity", slug: "relative_humidity", value: formatReading(humidity, "%"), hint: statusHint(humidity), muted: !humidity || humidity.status !== "fresh" },
        { name: "pH", slug: "water_ph", value: formatReading(ph, ""), hint: statusHint(ph), muted: !ph || ph.status !== "fresh" },
        { name: "EC", slug: "electrical_conductivity", value: formatReading(ec), hint: statusHint(ec), muted: !ec || ec.status !== "fresh" },
        { name: "Water Level", slug: "reservoir_water_level", value: formatReading(waterLevel, "cm"), hint: statusHint(waterLevel), muted: !waterLevel || waterLevel.status !== "fresh" },
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
                    to={`${history}?sensor=${card.slug}#sensor-history`}
                />
            ))}
        </div>
    )
}
