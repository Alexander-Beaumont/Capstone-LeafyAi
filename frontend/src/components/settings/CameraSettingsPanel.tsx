import { useContext, useEffect, useMemo, useState } from "react"
import Panel from "../primatives/Panel"
import IconTitle from "../primatives/IconTitle"
import Button from "../primatives/Button"
import Dropdown, { type dataFormat } from "../primatives/Dropdown"
import Switch from "../primatives/Switch"
import TextBox from "../primatives/Textbox"
import ConfirmDialog from "../primatives/ConfirmDialog"
import { LuCamera } from "react-icons/lu"
import { FarmOverviewContext } from "../../providers/FarmOverviewProvider"
import { userContext } from "../../providers/UserProvider"
import { captureFarmCamera, createFarmCamera, getFarmCameras, getFarmLevels, patchFarmCamera } from "../../util/api-service-layer"
import { formatTimestamp } from "../../util/operator"
import { toApiTime, toInputTime } from "../../util/ai-agent"
import type { CameraWrite, FarmCamera, FarmLevel } from "../../util/types"

interface Draft {
    farm_level_id: number
    name: string
    position: string
    ip_address: string
    rtsp_port: string
    rtsp_path: string
    enabled: boolean
    capture_interval_minutes: string
    active_start_time: string
    active_end_time: string
}

const emptyDraft: Draft = {
    farm_level_id: 0,
    name: "",
    position: "",
    ip_address: "",
    rtsp_port: "554",
    rtsp_path: "/stream1",
    enabled: true,
    capture_interval_minutes: "30",
    active_start_time: "",
    active_end_time: "",
}

function draftFrom(camera: FarmCamera): Draft {
    return {
        farm_level_id: camera.farm_level_id,
        name: camera.name,
        position: camera.position ?? "",
        ip_address: camera.ip_address ?? "",
        rtsp_port: camera.rtsp_port == null ? "" : String(camera.rtsp_port),
        rtsp_path: camera.rtsp_path ?? "",
        enabled: camera.enabled,
        capture_interval_minutes: String(camera.capture_interval_minutes),
        active_start_time: camera.active_start_time ? toInputTime(camera.active_start_time) : "",
        active_end_time: camera.active_end_time ? toInputTime(camera.active_end_time) : "",
    }
}

function windowValue(value: string) {
    return value.trim() ? toApiTime(value.trim()) : null
}

function validateDraft(draft: Draft) {
    const errors: string[] = []
    if (!draft.farm_level_id) errors.push("Choose a farm level.")
    if (!draft.name.trim()) errors.push("Name is required.")
    if (!draft.ip_address.trim()) errors.push("IP address is required.")
    const port = Number(draft.rtsp_port)
    if (!Number.isInteger(port) || port < 1) errors.push("RTSP port is required.")
    if (!draft.rtsp_path.trim()) errors.push("RTSP path is required.")
    const interval = Number(draft.capture_interval_minutes)
    if (!Number.isInteger(interval) || interval < 1) errors.push("Interval must be at least 1 minute.")
    const start = draft.active_start_time.trim()
    const end = draft.active_end_time.trim()
    if (Boolean(start) !== Boolean(end)) errors.push("Active start and end must both be set, or both be blank.")
    else if (start && end && toApiTime(start) === toApiTime(end)) errors.push("Active start and end must differ.")
    return errors
}

function writeBody(draft: Draft): CameraWrite {
    return {
        farm_level_id: draft.farm_level_id,
        name: draft.name.trim(),
        position: draft.position.trim(),
        source_type: "RTSP",
        ip_address: draft.ip_address.trim(),
        rtsp_port: Number(draft.rtsp_port),
        rtsp_path: draft.rtsp_path.trim(),
        enabled: draft.enabled,
        capture_interval_minutes: Number(draft.capture_interval_minutes),
        active_start_time: windowValue(draft.active_start_time),
        active_end_time: windowValue(draft.active_end_time),
    }
}

export default function CameraSettingsPanel() {
    const user = useContext(userContext)
    const overview = useContext(FarmOverviewContext)
    const [cameras, setCameras] = useState<FarmCamera[]>([])
    const [levels, setLevels] = useState<FarmLevel[]>([])
    const [drafts, setDrafts] = useState<Record<number, Draft>>({})
    const [createDraft, setCreateDraft] = useState<Draft>(emptyDraft)
    const [error, setError] = useState("")
    const [message, setMessage] = useState("")
    const [busy, setBusy] = useState(false)
    const [captureTarget, setCaptureTarget] = useState<FarmCamera | null>(null)
    const [loading, setLoading] = useState(true)

    const deviceIds = useMemo(
        () => new Set((overview.farmState?.devices ?? []).map(device => device.device_id)),
        [overview.farmState],
    )
    const farmLevels = deviceIds.size === 0 ? [] : levels.filter(level => deviceIds.has(level.device))
    const levelItems: dataFormat[] = farmLevels.map(level => ({
        id: level.id,
        name: `Level ${level.level_number}`,
    }))

    async function load() {
        if (!user.accessToken || overview.farmId == null) return
        setLoading(true)
        const [cameraResult, levelResult] = await Promise.all([
            getFarmCameras(user.accessToken, overview.farmId),
            getFarmLevels(user.accessToken),
        ])
        setLoading(false)
        if (!cameraResult.success || !cameraResult.data) {
            setError(cameraResult.msg)
            return
        }
        setCameras(cameraResult.data.results)
        setDrafts(Object.fromEntries(cameraResult.data.results.map(camera => [camera.id, draftFrom(camera)])))
        if (levelResult.success && Array.isArray(levelResult.data)) setLevels(levelResult.data)
        else if (!levelResult.success) setError(levelResult.msg)
    }

    useEffect(() => {
        if (!user.accessToken || overview.farmId == null) return
        let cancelled = false
        const token = user.accessToken
        const farmId = overview.farmId
        const run = async () => {
            const [cameraResult, levelResult] = await Promise.all([
                getFarmCameras(token, farmId),
                getFarmLevels(token),
            ])
            if (cancelled) return
            setLoading(false)
            if (!cameraResult.success || !cameraResult.data) {
                setError(cameraResult.msg)
                return
            }
            setCameras(cameraResult.data.results)
            setDrafts(Object.fromEntries(cameraResult.data.results.map(camera => [camera.id, draftFrom(camera)])))
            if (levelResult.success && Array.isArray(levelResult.data)) setLevels(levelResult.data)
            else if (!levelResult.success) setError(levelResult.msg)
        }
        run()
        return () => {
            cancelled = true
        }
    }, [user.accessToken, overview.farmId])

    function updateDraft(cameraId: number, patch: Partial<Draft>) {
        setDrafts(current => ({ ...current, [cameraId]: { ...current[cameraId], ...patch } }))
    }

    async function save(camera: FarmCamera) {
        if (!user.accessToken || overview.farmId == null) return
        const draft = drafts[camera.id]
        const problems = validateDraft(draft)
        if (problems.length) {
            setError(problems.join(" "))
            return
        }
        setBusy(true)
        setError("")
        const result = await patchFarmCamera(user.accessToken, overview.farmId, camera.id, writeBody(draft))
        setBusy(false)
        if (!result.success || !result.data) {
            setError(result.msg)
            return
        }
        setCameras(current => current.map(item => item.id === camera.id ? result.data! : item))
        setDrafts(current => ({ ...current, [camera.id]: draftFrom(result.data!) }))
        setMessage(`${result.data.name} saved.`)
    }

    async function archive(camera: FarmCamera) {
        if (!user.accessToken || overview.farmId == null) return
        setBusy(true)
        setError("")
        const result = await patchFarmCamera(user.accessToken, overview.farmId, camera.id, { is_archived: true })
        setBusy(false)
        if (!result.success) {
            setError(result.msg)
            return
        }
        setCameras(current => current.filter(item => item.id !== camera.id))
        setMessage(`${camera.name} archived.`)
    }

    async function capture(camera: FarmCamera) {
        if (!user.accessToken || overview.farmId == null) return
        setBusy(true)
        setError("")
        const result = await captureFarmCamera(user.accessToken, overview.farmId, camera.id)
        setBusy(false)
        if (!result.success) {
            setError(result.msg)
            return
        }
        setMessage(`Captured image ${result.data?.id ?? ""} for ${camera.name}.`)
        await load()
    }

    async function create() {
        if (!user.accessToken || overview.farmId == null) return
        const problems = validateDraft(createDraft)
        if (problems.length) {
            setError(problems.join(" "))
            return
        }
        setBusy(true)
        setError("")
        const result = await createFarmCamera(user.accessToken, overview.farmId, { ...writeBody(createDraft), enabled: true })
        setBusy(false)
        if (!result.success || !result.data) {
            setError(result.msg)
            return
        }
        setCameras(current => [...current, result.data!])
        setDrafts(current => ({ ...current, [result.data!.id]: draftFrom(result.data!) }))
        setCreateDraft({ ...emptyDraft, farm_level_id: createDraft.farm_level_id })
        setMessage(`${result.data.name} created.`)
    }

    function fields(draft: Draft, onChange: (patch: Partial<Draft>) => void, includeEnabled = true) {
        const selectedLevel = levelItems.find(item => item.id === draft.farm_level_id) ?? null
        return (
            <div className="flex flex-col gap-3">
                <Dropdown
                    items={levelItems}
                    selectedItem={selectedLevel}
                    setSelectedItem={id => onChange({ farm_level_id: id })}
                    defaultText="Farm level"
                    showIcon
                />
                <TextBox name="Name" value={draft.name} setValue={value => onChange({ name: value })} charLimit={255} placeHolder="Top level" />
                <TextBox name="Position" value={draft.position} setValue={value => onChange({ position: value })} charLimit={100} placeHolder="front" />
                <TextBox name="IP address" value={draft.ip_address} setValue={value => onChange({ ip_address: value })} charLimit={64} placeHolder="192.168.1.108" />
                <TextBox name="Interval (minutes)" value={draft.capture_interval_minutes} setValue={value => onChange({ capture_interval_minutes: value })} charLimit={5} placeHolder="30" numeric />
                <div className="grid gap-3 sm:grid-cols-2">
                    <TextBox name="RTSP port" value={draft.rtsp_port} setValue={value => onChange({ rtsp_port: value })} charLimit={5} placeHolder="554" numeric />
                    <TextBox name="RTSP path" value={draft.rtsp_path} setValue={value => onChange({ rtsp_path: value })} charLimit={255} placeHolder="/stream1" />
                    {includeEnabled ?
                        <div className="flex items-center justify-between bg-panel2 border border-border rounded-lg px-3">
                            <p className="text-sm text-subtext1">Enabled</p>
                            <Switch ticked={draft.enabled} setTicked={enabled => onChange({ enabled })} />
                        </div>
                    : null}
                    <TextBox name="Active start" value={draft.active_start_time} setValue={value => onChange({ active_start_time: value })} charLimit={5} placeHolder="06:00" />
                    <TextBox name="Active end" value={draft.active_end_time} setValue={value => onChange({ active_end_time: value })} charLimit={5} placeHolder="22:00" />
                </div>
            </div>
        )
    }

    return (
        <Panel styles="w-full p-3 px-4 flex flex-col gap-4">
            <IconTitle title="Cameras" icon={<LuCamera size={16} />} />
            {!overview.farmId ?
                <p className="text-sm text-subtext3">Select a farm to manage cameras.</p>
            : loading && cameras.length === 0 ?
                <div className="h-24 bg-panel2 animate-pulse rounded-md" />
            : <>
                {cameras.length === 0 ? <p className="text-sm text-subtext3">No active cameras.</p> : null}
                {cameras.map(camera => {
                    const draft = drafts[camera.id] ?? draftFrom(camera)
                    return (
                        <div key={camera.id} className="border border-border rounded-lg p-3 flex flex-col gap-3">
                            <div className="flex flex-wrap items-baseline justify-between gap-2">
                                <p className="text-sm text-title font-semibold">{camera.name}</p>
                                <p className="text-xs text-subtext3">{camera.schedule_state}</p>
                            </div>
                            <p className="text-xs text-subtext3">
                                Last capture {formatTimestamp(camera.last_capture_at)} · next {formatTimestamp(camera.next_scheduled_capture)}
                                {camera.image_quality ? ` · ${camera.image_quality.status}` : ""}
                            </p>
                            {fields(draft, patch => updateDraft(camera.id, patch))}
                            <div className="flex flex-wrap gap-3">
                                <Button name="Save" highlight loading={busy} onSubmit={() => save(camera)} />
                                <Button name="Capture" highlight={false} loading={busy && captureTarget?.id === camera.id} onSubmit={() => setCaptureTarget(camera)} />
                                <Button name="Archive" highlight={false} loading={busy} onSubmit={() => archive(camera)} />
                            </div>
                        </div>
                    )
                })}
                <div className="border border-border rounded-lg p-3 flex flex-col gap-3">
                    <p className="text-sm text-title font-semibold">Add camera</p>
                    <p className="text-xs text-subtext3">Only RTSP cameras can be added. Leave both active times blank for 24-hour capture.</p>
                    {fields(createDraft, patch => setCreateDraft(current => ({ ...current, ...patch })), false)}
                    <Button name="Create camera" highlight loading={busy} onSubmit={create} />
                </div>
            </>}
            {error ? <p className="text-xs text-high">{error}</p> : null}
            {message ? <p className="text-xs text-low">{message}</p> : null}
            <ConfirmDialog
                open={captureTarget != null}
                title="Capture image?"
                text={`Capture an image from ${captureTarget?.name ?? "this camera"}.`}
                confirm="Capture"
                busy={busy}
                onConfirm={() => {
                    if (!captureTarget) return
                    const target = captureTarget
                    void capture(target).then(() => setCaptureTarget(current => current?.id === target.id ? null : current))
                }}
                onClose={() => setCaptureTarget(null)}
            />
        </Panel>
    )
}
