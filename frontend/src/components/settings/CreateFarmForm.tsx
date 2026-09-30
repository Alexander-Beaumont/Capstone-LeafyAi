import { useContext, useState } from "react"
import Button from "../primatives/Button"
import TextBox from "../primatives/Textbox"
import Modal from "../primatives/Modal"
import { userContext } from "../../providers/UserProvider"
import { FarmOverviewContext } from "../../providers/FarmOverviewProvider"
import { createFarmWithLayout } from "../../util/api-service-layer"

const SETUP_ITEMS = [
    "Sensor ingest, on this page: enter the water-quality URL and the ambient-sensor URL, then turn ingestion on. Test and Collect stay unavailable until both URLs are set and the switch is on.",
    "Cameras, on this page: add an RTSP camera if this farm should capture images.",
    "Growing areas, on Growth & Harvesting: levels 1 and 2 exist, and trays and batches are added there.",
    "AI, on this page: the schedule is off and the provider is the mock default. Set a real provider and turn the schedule on if this farm should produce recommendations.",
]

export default function CreateFarmForm() {
    const user = useContext(userContext)
    const overview = useContext(FarmOverviewContext)
    const [name, setName] = useState("")
    const [location, setLocation] = useState("")
    const [error, setError] = useState("")
    const [busy, setBusy] = useState(false)
    const [setupOpen, setSetupOpen] = useState(false)

    async function submit() {
        const trimmed = name.trim()
        if (!trimmed) {
            setError("Enter a farm name")
            return
        }
        if (!user.accessToken) return
        setBusy(true)
        setError("")
        const result = await createFarmWithLayout(user.accessToken, trimmed, location.trim())
        setBusy(false)
        if (result.data) {
            overview.selectFarm(result.data)
            setName("")
            setLocation("")
        }
        if (result.success) setSetupOpen(true)
        else setError(result.msg || "Could not create the farm")
    }

    return (
        <div className="flex flex-col gap-3">
            <TextBox name="Name" charLimit={255} value={name} setValue={setName} placeHolder="North rack" />
            <TextBox name="Location" charLimit={255} value={location} setValue={setLocation} placeHolder="Lab" />
            {error ? <p className="text-xs text-red-400">{error}</p> : null}
            <Button name="Create farm" highlight loading={busy} onSubmit={submit} styles={{ fullWidth: true }} />
            <Modal open={setupOpen} onClose={() => setSetupOpen(false)}>
                <div className="bg-panel1 border border-border p-5 flex flex-col rounded-xl w-[80%] max-w-xl gap-3">
                    <p className="text-xl font-semibold text-title">Farm created</p>
                    <p className="text-sm text-subtext1">
                        This farm has a controller, standard sensors, and levels 1 and 2. Add the endpoint details before it can collect data.
                    </p>
                    <ul className="flex flex-col gap-2 text-sm text-subtext1 list-disc pl-5">
                        {SETUP_ITEMS.map(item => <li key={item}>{item}</li>)}
                    </ul>
                    <Button
                        name="Close"
                        highlight
                        styles={{ fullWidth: false, noAnimation: true }}
                        onSubmit={() => setSetupOpen(false)}
                    />
                </div>
            </Modal>
        </div>
    )
}
