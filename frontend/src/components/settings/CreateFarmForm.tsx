import { useContext, useState } from "react"
import Button from "../primatives/Button"
import TextBox from "../primatives/Textbox"
import { userContext } from "../../providers/UserProvider"
import { FarmOverviewContext } from "../../providers/FarmOverviewProvider"
import { createFarmWithLayout } from "../../util/api-service-layer"

export default function CreateFarmForm() {
    const user = useContext(userContext)
    const overview = useContext(FarmOverviewContext)
    const [name, setName] = useState("")
    const [location, setLocation] = useState("")
    const [error, setError] = useState("")
    const [busy, setBusy] = useState(false)

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
        if (!result.success) setError(result.msg || "Could not create the farm")
    }

    return (
        <div className="flex flex-col gap-3">
            <TextBox name="Name" charLimit={255} value={name} setValue={setName} placeHolder="North rack" />
            <TextBox name="Location" charLimit={255} value={location} setValue={setLocation} placeHolder="Lab" />
            {error ? <p className="text-xs text-red-400">{error}</p> : null}
            <Button name="Create farm" highlight loading={busy} onSubmit={submit} styles={{ fullWidth: true }} />
        </div>
    )
}
