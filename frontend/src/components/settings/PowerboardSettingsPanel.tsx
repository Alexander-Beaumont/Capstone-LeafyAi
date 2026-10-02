import { useContext, useEffect, useMemo, useState } from "react"
import { GoGear } from "react-icons/go"
import { FarmOverviewContext } from "../../providers/FarmOverviewProvider"
import { userContext } from "../../providers/UserProvider"
import { getFarmPowerboardConfiguration, patchFarmPowerboardConfiguration } from "../../util/api-service-layer"
import type { PowerboardConfiguration } from "../../util/types"
import Button from "../primatives/Button"
import IconTitle from "../primatives/IconTitle"
import Panel from "../primatives/Panel"
import TextBox from "../primatives/Textbox"

function looksLikeIpv4(value: string) {
    if (!value.trim()) return false
    const parts = value.split(".")
    if (parts.length !== 4) return true
    return parts.some(part => !/^\d{1,3}$/.test(part) || Number(part) > 255)
}

export default function PowerboardSettingsPanel() {
    const user = useContext(userContext)
    const overview = useContext(FarmOverviewContext)
    const [config, setConfig] = useState<PowerboardConfiguration | null>(null)
    const [board1, setBoard1] = useState("")
    const [board2, setBoard2] = useState("")
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState("")
    const [message, setMessage] = useState("")

    useEffect(() => {
        if (!user.accessToken || overview.farmId == null) {
            setLoading(false)
            return
        }
        let cancelled = false
        setLoading(true)
        setError("")
        setMessage("")
        getFarmPowerboardConfiguration(user.accessToken, overview.farmId).then(result => {
            if (cancelled) return
            setLoading(false)
            if (!result.success || !result.data) {
                setError(result.msg || "Could not load Powerboard configuration.")
                return
            }
            setConfig(result.data)
            setBoard1(result.data.powerboard_1_ip ?? "")
            setBoard2(result.data.powerboard_2_ip ?? "")
        })
        return () => { cancelled = true }
    }, [user.accessToken, overview.farmId])

    const changed = useMemo(() => {
        if (!config) return false
        return board1 !== (config.powerboard_1_ip ?? "") || board2 !== (config.powerboard_2_ip ?? "")
    }, [config, board1, board2])

    async function save() {
        if (!user.accessToken || overview.farmId == null || !config || !changed) return
        setSaving(true)
        setError("")
        setMessage("")
        const result = await patchFarmPowerboardConfiguration(user.accessToken, overview.farmId, {
            powerboard_1_ip: board1.trim() || null,
            powerboard_2_ip: board2.trim() || null,
        })
        setSaving(false)
        if (!result.success || !result.data) {
            setError(result.msg || "Could not save Powerboard configuration.")
            return
        }
        setConfig(result.data)
        setBoard1(result.data.powerboard_1_ip ?? "")
        setBoard2(result.data.powerboard_2_ip ?? "")
        setMessage("Powerboard configuration saved.")
    }

    return (
        <Panel styles="w-full p-3 px-4 flex flex-col gap-4">
            <IconTitle title="Powerboard configuration" icon={<GoGear />} />
            {overview.farmId == null ?
                <p className="text-sm text-subtext3">Select a farm to configure its Powerboards.</p>
            : loading ?
                <div className="h-24 bg-panel2 animate-pulse rounded-md" />
            : <>
                <p className="text-xs text-subtext3">
                    Enter the IP address of the two physical Powerboards for this farm. The existing outlet/device mapping stays unchanged.
                </p>
                <div className="grid gap-3 sm:grid-cols-2">
                    <TextBox
                        name="Powerboard 1 IP address"
                        value={board1}
                        setValue={setBoard1}
                        charLimit={45}
                        placeHolder="192.168.1.102"
                        invalidFunc={looksLikeIpv4}
                    />
                    <TextBox
                        name="Powerboard 2 IP address"
                        value={board2}
                        setValue={setBoard2}
                        charLimit={45}
                        placeHolder="192.168.1.101"
                        invalidFunc={looksLikeIpv4}
                    />
                </div>
                {error ? <p className="text-xs text-high">{error}</p> : null}
                {message ? <p className="text-xs text-low">{message}</p> : null}
                <div className="flex items-center gap-3">
                    <Button name="Save" highlight loading={saving} onSubmit={() => { void save() }} />
                    {changed ? <p className="text-xs text-subtext3">Unsaved changes</p> : null}
                </div>
            </>}
        </Panel>
    )
}
