import { useContext, useEffect, useState } from "react"
import Panel from "../primatives/Panel"
import IconTitle from "../primatives/IconTitle"
import Button from "../primatives/Button"
import Switch from "../primatives/Switch"
import TextBox from "../primatives/Textbox"
import { GoGear } from "react-icons/go"
import { FarmOverviewContext } from "../../providers/FarmOverviewProvider"
import { userContext } from "../../providers/UserProvider"
import { collectSensorIngest, getSensorIngest, patchSensorIngest, testSensorIngest } from "../../util/api-service-layer"
import { formatTimestamp } from "../../util/operator"
import type { SensorCollectionResult, SensorIngestConfiguration, SensorIngestPatch } from "../../util/types"

interface Draft {
    enabled: boolean
    water_quality_url: string
    ambient_sensor_url: string
    poll_interval_seconds: string
    sensor_stale_threshold_seconds: string
}

function draftFrom(config: SensorIngestConfiguration): Draft {
    return {
        enabled: config.enabled,
        water_quality_url: config.water_quality_url,
        ambient_sensor_url: config.ambient_sensor_url,
        poll_interval_seconds: String(config.poll_interval_seconds),
        sensor_stale_threshold_seconds: String(config.sensor_stale_threshold_seconds),
    }
}

function patchFrom(config: SensorIngestConfiguration, draft: Draft): SensorIngestPatch {
    const patch: SensorIngestPatch = {}
    if (draft.enabled !== config.enabled) patch.enabled = draft.enabled
    if (draft.water_quality_url !== config.water_quality_url) patch.water_quality_url = draft.water_quality_url
    if (draft.ambient_sensor_url !== config.ambient_sensor_url) patch.ambient_sensor_url = draft.ambient_sensor_url
    const poll = Number(draft.poll_interval_seconds)
    const stale = Number(draft.sensor_stale_threshold_seconds)
    if (poll !== config.poll_interval_seconds) patch.poll_interval_seconds = poll
    if (stale !== config.sensor_stale_threshold_seconds) patch.sensor_stale_threshold_seconds = stale
    return patch
}

export default function SensorIngestPanel() {
    const user = useContext(userContext)
    const overview = useContext(FarmOverviewContext)
    const [configs, setConfigs] = useState<SensorIngestConfiguration[]>([])
    const [drafts, setDrafts] = useState<Record<number, Draft>>({})
    const [messages, setMessages] = useState<Record<number, string>>({})
    const [errors, setErrors] = useState<Record<number, string>>({})
    const [busyId, setBusyId] = useState<number | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (!user.accessToken || overview.farmId == null) return
        let cancelled = false
        const token = user.accessToken
        const farmId = overview.farmId
        const run = async () => {
            const result = await getSensorIngest(token, farmId)
            if (cancelled) return
            setLoading(false)
            if (!result.success || !result.data) {
                setErrors({ 0: result.msg })
                return
            }
            setConfigs(result.data.results)
            setDrafts(Object.fromEntries(result.data.results.map(config => [config.device_id, draftFrom(config)])))
        }
        run()
        return () => {
            cancelled = true
        }
    }, [user.accessToken, overview.farmId])

    function updateDraft(deviceId: number, patch: Partial<Draft>) {
        setDrafts(current => ({ ...current, [deviceId]: { ...current[deviceId], ...patch } }))
    }

    function showResult(deviceId: number, result: SensorCollectionResult) {
        const missing = result.missing_sensors.length ? ` Missing: ${result.missing_sensors.join(", ")}.` : ""
        const invalid = result.invalid_sensors.length ? ` Invalid: ${result.invalid_sensors.join(", ")}.` : ""
        setMessages(current => ({
            ...current,
            [deviceId]: `Stored ${result.stored_count}.${missing}${invalid}`,
        }))
    }

    async function save(config: SensorIngestConfiguration) {
        if (!user.accessToken || overview.farmId == null) return
        const draft = drafts[config.device_id]
        const patch = patchFrom(config, draft)
        if (Object.keys(patch).length === 0) return
        setBusyId(config.device_id)
        setErrors(current => ({ ...current, [config.device_id]: "" }))
        const result = await patchSensorIngest(user.accessToken, overview.farmId, config.device_id, patch)
        setBusyId(null)
        if (!result.success || !result.data) {
            setErrors(current => ({ ...current, [config.device_id]: result.msg }))
            return
        }
        setConfigs(current => current.map(item => item.device_id === config.device_id ? result.data! : item))
        setDrafts(current => ({ ...current, [config.device_id]: draftFrom(result.data!) }))
        setMessages(current => ({ ...current, [config.device_id]: "Ingest settings saved." }))
        overview.setUpdate(Math.random())
    }

    async function runOperation(config: SensorIngestConfiguration, mode: "test" | "collect") {
        if (!user.accessToken || overview.farmId == null) return
        setBusyId(config.device_id)
        setErrors(current => ({ ...current, [config.device_id]: "" }))
        const result = mode === "test"
            ? await testSensorIngest(user.accessToken, overview.farmId, config.device_id)
            : await collectSensorIngest(user.accessToken, overview.farmId, config.device_id)
        setBusyId(null)
        if (!result.success || !result.data) {
            setErrors(current => ({ ...current, [config.device_id]: result.msg }))
            return
        }
        if (result.data.ingest_status) {
            setConfigs(current => current.map(item => item.device_id === config.device_id ? result.data!.ingest_status : item))
        }
        showResult(config.device_id, result.data)
    }

    return (
        <Panel styles="w-full p-3 px-4 flex flex-col gap-4">
            <IconTitle title="Sensor ingestion" icon={<GoGear />} />
            {!overview.farmId ?
                <p className="text-sm text-subtext3">Select a farm to edit ingestion.</p>
            : loading && configs.length === 0 ?
                <div className="h-24 bg-panel2 animate-pulse rounded-md" />
            : configs.length === 0 ?
                <p className="text-sm text-subtext3">No sensor ingestion configuration exists for this farm.</p>
            : configs.map(config => {
                const draft = drafts[config.device_id] ?? draftFrom(config)
                const changed = Object.keys(patchFrom(config, draft)).length > 0
                return (
                    <div key={config.device_id} className="border border-border rounded-lg p-3 flex flex-col gap-3">
                        <div>
                            <p className="text-sm text-title font-semibold">{config.device_name}</p>
                            <p className="text-xs text-subtext3">{config.device_slug}</p>
                        </div>
                        <div className="flex items-center justify-between bg-panel2 border border-border rounded-lg p-3">
                            <p className="text-sm text-subtext1">Enabled</p>
                            <Switch ticked={draft.enabled} setTicked={enabled => updateDraft(config.device_id, { enabled })} />
                        </div>
                        <TextBox name="Water quality URL" value={draft.water_quality_url} setValue={value => updateDraft(config.device_id, { water_quality_url: value })} charLimit={500} placeHolder="http://192.168.1.20/readings" />
                        <TextBox name="Ambient sensor URL" value={draft.ambient_sensor_url} setValue={value => updateDraft(config.device_id, { ambient_sensor_url: value })} charLimit={500} placeHolder="http://192.168.1.21/readings" />
                        <div className="grid gap-3 sm:grid-cols-2">
                            <TextBox name="Poll interval (seconds)" value={draft.poll_interval_seconds} setValue={value => updateDraft(config.device_id, { poll_interval_seconds: value })} charLimit={6} placeHolder="30" numeric />
                            <TextBox name="Stale after (seconds)" value={draft.sensor_stale_threshold_seconds} setValue={value => updateDraft(config.device_id, { sensor_stale_threshold_seconds: value })} charLimit={7} placeHolder="120" numeric />
                        </div>
                        <p className="text-xs text-subtext3">
                            Last success {formatTimestamp(config.last_success_at)} · failures {config.consecutive_failures}
                        </p>
                        {config.last_error ? <p className="text-xs text-high">{config.last_error}</p> : null}
                        {errors[config.device_id] ? <p className="text-xs text-high">{errors[config.device_id]}</p> : null}
                        {messages[config.device_id] ? <p className="text-xs text-low">{messages[config.device_id]}</p> : null}
                        <div className="flex flex-wrap gap-3">
                            <Button name="Save" highlight loading={busyId === config.device_id} onSubmit={() => save(config)} />
                            <Button name="Test" highlight={false} loading={busyId === config.device_id} onSubmit={() => runOperation(config, "test")} />
                            <Button name="Collect" highlight={false} loading={busyId === config.device_id} onSubmit={() => runOperation(config, "collect")} />
                        </div>
                        {!changed ? null : <p className="text-xs text-subtext3">Unsaved changes</p>}
                    </div>
                )
            })}
            {errors[0] ? <p className="text-xs text-high">{errors[0]}</p> : null}
        </Panel>
    )
}
