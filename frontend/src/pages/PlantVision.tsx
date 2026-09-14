import { useContext, useEffect, useMemo, useRef, useState, type PointerEvent } from "react"
import { PiPlant } from "react-icons/pi"
import PageTitlePanel from "../components/primatives/PageTitlePanel"
import Panel from "../components/primatives/Panel"
import IconTitle from "../components/primatives/IconTitle"
import { userContext } from "../providers/UserProvider"
import {
    createCamera,
    getCameras,
    getFarmLevels,
    getLatestAnalysis,
    getLatestImage,
    patchCamera,
} from "../util/api-service-layer"
import { BACKEND_BASEURL } from "../util/constants"
import type { Camera, CameraInput, FarmLevel, LatestAnalysis, LatestImage, RoiRect } from "../util/types"

type Period = "AM" | "PM"
type TimeParts = { hour: number; minute: number; period: Period }

const nowIso = () => new Date().toISOString()
const clamp = (value: number) => Math.max(0, Math.min(1, value))
const HOURS = Array.from({ length: 12 }, (_, index) => index + 1)
const MINUTES = Array.from({ length: 60 }, (_, index) => index)

function absoluteImageUrl(value: string) {
    if (!value) return ""
    if (value.startsWith("http://") || value.startsWith("https://")) return value
    return `${BACKEND_BASEURL}/${value.replace(/^\//, "")}`
}

function metric(value: string | null, suffix = "%") {
    if (value === null || value === undefined) return "N/A"
    return `${Number(value).toFixed(2)}${suffix}`
}

function parseTime24(value: string | null, fallback: TimeParts): TimeParts {
    if (!value) return fallback
    const [rawHour = "0", rawMinute = "0"] = value.split(":")
    const hour24 = Math.max(0, Math.min(23, Number(rawHour)))
    const minute = Math.max(0, Math.min(59, Number(rawMinute)))
    return {
        hour: hour24 % 12 || 12,
        minute,
        period: hour24 >= 12 ? "PM" : "AM",
    }
}

function toTime24(parts: TimeParts) {
    let hour24 = parts.hour % 12
    if (parts.period === "PM") hour24 += 12
    return `${String(hour24).padStart(2, "0")}:${String(parts.minute).padStart(2, "0")}:00`
}

function formatTime12(value: string | null) {
    if (!value) return ""
    const parts = parseTime24(value, { hour: 12, minute: 0, period: "AM" })
    return `${parts.hour}:${String(parts.minute).padStart(2, "0")} ${parts.period}`
}

function formatDateTimeEnglish(value: string) {
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    const day = String(date.getDate()).padStart(2, "0")
    const month = String(date.getMonth() + 1).padStart(2, "0")
    const year = date.getFullYear()
    const hour24 = date.getHours()
    const hour12 = hour24 % 12 || 12
    const period: Period = hour24 >= 12 ? "PM" : "AM"
    const minute = String(date.getMinutes()).padStart(2, "0")
    const second = String(date.getSeconds()).padStart(2, "0")
    return `${day}/${month}/${year} ${hour12}:${minute}:${second} ${period}`
}

function Time12HourInput({
    label,
    value,
    onChange,
    disabled = false,
    fallback,
}: {
    label: string
    value: string | null
    onChange: (value: string) => void
    disabled?: boolean
    fallback: TimeParts
}) {
    const parts = parseTime24(value, fallback)
    const update = (next: Partial<TimeParts>) => onChange(toTime24({ ...parts, ...next }))

    return (
        <fieldset className="min-w-0">
            <legend className="text-xs text-subtext2 mb-1">{label}</legend>
            <div className="grid grid-cols-[1fr_1fr_1.1fr] gap-1">
                <select
                    aria-label={`${label} hour`}
                    disabled={disabled}
                    value={parts.hour}
                    onChange={event => update({ hour: Number(event.target.value) })}
                    className="min-w-0 bg-panel1 border border-border rounded p-2 text-subtext1 disabled:opacity-50"
                >
                    {HOURS.map(hour => <option key={hour} value={hour}>{String(hour).padStart(2, "0")}</option>)}
                </select>
                <select
                    aria-label={`${label} minute`}
                    disabled={disabled}
                    value={parts.minute}
                    onChange={event => update({ minute: Number(event.target.value) })}
                    className="min-w-0 bg-panel1 border border-border rounded p-2 text-subtext1 disabled:opacity-50"
                >
                    {MINUTES.map(minute => <option key={minute} value={minute}>{String(minute).padStart(2, "0")}</option>)}
                </select>
                <select
                    aria-label={`${label} AM or PM`}
                    disabled={disabled}
                    value={parts.period}
                    onChange={event => update({ period: event.target.value as Period })}
                    className="min-w-0 bg-panel1 border border-border rounded p-2 text-subtext1 disabled:opacity-50"
                >
                    <option value="AM">AM</option>
                    <option value="PM">PM</option>
                </select>
            </div>
        </fieldset>
    )
}

function cameraToInput(camera: Camera): CameraInput {
    return {
        farm_level_id: camera.farm_level_id,
        name: camera.name,
        position: camera.position,
        source_type: camera.source_type,
        ip_address: camera.ip_address,
        rtsp_port: camera.rtsp_port,
        rtsp_path: camera.rtsp_path,
        enabled: camera.enabled,
        cv_enabled: camera.cv_enabled,
        capture_interval_minutes: camera.capture_interval_minutes,
        active_start_time: camera.active_start_time,
        active_end_time: camera.active_end_time,
        roi_points: camera.roi_points,
        is_archived: camera.is_archived,
    }
}

const initialForm: CameraInput = {
    farm_level_id: 0,
    name: "",
    position: "",
    source_type: "RTSP",
    ip_address: null,
    rtsp_port: null,
    rtsp_path: null,
    enabled: true,
    cv_enabled: true,
    capture_interval_minutes: 30,
    active_start_time: null,
    active_end_time: null,
    roi_points: null,
    is_archived: false,
}

function CameraSettingsFields({
    value,
    onChange,
    farmLevels,
    includeIdentity = true,
}: {
    value: CameraInput
    onChange: (next: CameraInput) => void
    farmLevels: FarmLevel[]
    includeIdentity?: boolean
}) {
    const is24Hours = value.active_start_time === null && value.active_end_time === null
    const set = (patch: Partial<CameraInput>) => onChange({ ...value, ...patch })

    return (
        <>
            {includeIdentity && (
                <>
                    <label className="text-xs text-subtext2">Name
                        <input value={value.name} onChange={event => set({ name: event.target.value })} className="mt-1 w-full bg-panel1 border border-border rounded p-2 text-subtext1" />
                    </label>
                    <label className="text-xs text-subtext2">Farm level
                        <select value={value.farm_level_id} onChange={event => set({ farm_level_id: Number(event.target.value) })} className="mt-1 w-full bg-panel1 border border-border rounded p-2 text-subtext1">
                            {farmLevels.map(level => <option key={level.id} value={level.id}>Level {level.level_number} (ID {level.id})</option>)}
                        </select>
                    </label>
                    <label className="text-xs text-subtext2">Position / Growth Area
                        <input value={value.position || ""} onChange={event => set({ position: event.target.value })} className="mt-1 w-full bg-panel1 border border-border rounded p-2 text-subtext1" placeholder="Top-down over Growth Area A" />
                    </label>
                </>
            )}

            <label className="text-xs text-subtext2">Source
                <input value="RTSP" readOnly className="mt-1 w-full bg-panel1 border border-border rounded p-2 text-subtext1 opacity-80" />
            </label>

            <label className="text-xs text-subtext2">IP address
                <input value={value.ip_address || ""} onChange={event => set({ ip_address: event.target.value })} className="mt-1 w-full bg-panel1 border border-border rounded p-2 text-subtext1" placeholder="e.g. 192.168.1.50" />
            </label>
            <label className="text-xs text-subtext2">RTSP port
                <input min={1} max={65535} type="number" value={value.rtsp_port ?? ""} onChange={event => set({ rtsp_port: event.target.value === "" ? null : Number(event.target.value) })} className="mt-1 w-full bg-panel1 border border-border rounded p-2 text-subtext1" placeholder="e.g. 554" />
            </label>
            <label className="text-xs text-subtext2 md:col-span-2">RTSP path
                <input value={value.rtsp_path || ""} onChange={event => set({ rtsp_path: event.target.value })} className="mt-1 w-full bg-panel1 border border-border rounded p-2 text-subtext1" placeholder="/stream1" />
            </label>

            <label className="text-xs text-subtext2">Capture interval (minutes)
                <input min={1} type="number" value={value.capture_interval_minutes} onChange={event => set({ capture_interval_minutes: Number(event.target.value) })} className="mt-1 w-full bg-panel1 border border-border rounded p-2 text-subtext1" />
            </label>

            <label className="text-xs text-subtext2 flex items-center gap-2 md:col-span-2 border border-border rounded p-2 bg-panel1">
                <input
                    type="checkbox"
                    checked={is24Hours}
                    onChange={event => set(event.target.checked
                        ? { active_start_time: null, active_end_time: null }
                        : { active_start_time: "08:00:00", active_end_time: "20:00:00" })}
                />
                24-hour capture eligibility
            </label>

            {!is24Hours && (
                <>
                    <Time12HourInput label="Active start" value={value.active_start_time} onChange={active_start_time => set({ active_start_time })} fallback={{ hour: 8, minute: 0, period: "AM" }} />
                    <Time12HourInput label="Active end" value={value.active_end_time} onChange={active_end_time => set({ active_end_time })} fallback={{ hour: 8, minute: 0, period: "PM" }} />
                </>
            )}
        </>
    )
}

export default function PlantVision() {
    const user = useContext(userContext)
    const [cameras, setCameras] = useState<Camera[]>([])
    const [farmLevels, setFarmLevels] = useState<FarmLevel[]>([])
    const [selectedId, setSelectedId] = useState<number | null>(null)
    const [latestImage, setLatestImage] = useState<LatestImage | null>(null)
    const [latestAnalysis, setLatestAnalysis] = useState<LatestAnalysis | null>(null)
    const [pageError, setPageError] = useState("")
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [showCreate, setShowCreate] = useState(false)
    const [showEdit, setShowEdit] = useState(false)
    const [form, setForm] = useState<CameraInput>(initialForm)
    const [editForm, setEditForm] = useState<CameraInput>(initialForm)
    const [resetForViewChange, setResetForViewChange] = useState(false)
    const [draftRoi, setDraftRoi] = useState<RoiRect | null>(null)
    const [dragStart, setDragStart] = useState<{ x: number; y: number } | null>(null)
    const imageRef = useRef<HTMLImageElement>(null)

    const selected = useMemo(
        () => cameras.find(camera => camera.id === selectedId) || null,
        [cameras, selectedId],
    )

    const loadCameras = async () => {
        if (!user.accessToken) return
        const [cameraResult, levelResult] = await Promise.all([
            getCameras(user.accessToken),
            getFarmLevels(user.accessToken),
        ])
        if (!cameraResult.success || !levelResult.success) {
            setPageError(cameraResult.msg || levelResult.msg)
            setLoading(false)
            return
        }
        const nextCameras = (cameraResult.data || []).filter(camera => !camera.is_archived)
        const levels = levelResult.data || []
        setCameras(nextCameras)
        setFarmLevels(levels)
        setSelectedId(current => current && nextCameras.some(camera => camera.id === current) ? current : nextCameras[0]?.id ?? null)
        setForm(current => ({ ...current, farm_level_id: current.farm_level_id || levels[0]?.id || 0 }))
        setPageError("")
        setLoading(false)
    }

    const refreshVision = async (cameraId: number) => {
        if (!user.accessToken) return
        const [imageResult, analysisResult] = await Promise.all([
            getLatestImage(user.accessToken, cameraId),
            getLatestAnalysis(user.accessToken, cameraId),
        ])
        setLatestImage(imageResult.success ? imageResult.data || null : null)
        setLatestAnalysis(analysisResult.success ? analysisResult.data || null : null)
        if (!imageResult.success && imageResult.status !== 404) setPageError(imageResult.msg)
        else if (!analysisResult.success && analysisResult.status !== 404) setPageError(analysisResult.msg)
        else setPageError("")
    }

    useEffect(() => { loadCameras() }, [user.accessToken])

    useEffect(() => {
        if (!selectedId) {
            setLatestImage(null)
            setLatestAnalysis(null)
            return
        }
        setDraftRoi(null)
        setLatestImage(null)
        setLatestAnalysis(null)
        setShowEdit(false)
        setResetForViewChange(false)
        refreshVision(selectedId)
        const timer = window.setInterval(() => refreshVision(selectedId), 15_000)
        return () => window.clearInterval(timer)
    }, [selectedId, user.accessToken])

    useEffect(() => {
        if (selected) setEditForm(cameraToInput(selected))
    }, [selected])

    const createNewCamera = async () => {
        if (!user.accessToken || !form.farm_level_id || !form.name.trim()) return
        setSaving(true)
        const payload: CameraInput = {
            ...form,
            name: form.name.trim(),
            position: form.position?.trim() || null,
            ip_address: form.ip_address?.trim() || null,
            rtsp_port: form.rtsp_port,
            rtsp_path: form.rtsp_path?.trim() || null,
            is_archived: false,
        }
        const result = await createCamera(user.accessToken, payload)
        setSaving(false)
        if (!result.success || !result.data) {
            setPageError(result.msg)
            return
        }
        setShowCreate(false)
        setForm({ ...initialForm, farm_level_id: farmLevels[0]?.id || 0 })
        await loadCameras()
        setSelectedId(result.data.id)
    }

    const updateSelected = async (patch: Partial<CameraInput>) => {
        if (!user.accessToken || !selected) return false
        setSaving(true)
        const result = await patchCamera(user.accessToken, selected.id, patch)
        setSaving(false)
        if (!result.success || !result.data) {
            setPageError(result.msg)
            return false
        }
        setCameras(current => current.map(camera => camera.id === result.data!.id ? result.data! : camera))
        setPageError("")
        return true
    }

    const saveCameraSettings = async () => {
        if (!selected || !user.accessToken) return
        const patch: Partial<CameraInput> = {
            farm_level_id: editForm.farm_level_id,
            name: editForm.name.trim(),
            position: editForm.position?.trim() || null,
            source_type: editForm.source_type,
            ip_address: editForm.ip_address?.trim() || null,
            rtsp_port: editForm.rtsp_port,
            rtsp_path: editForm.rtsp_path?.trim() || null,
            capture_interval_minutes: editForm.capture_interval_minutes,
            active_start_time: editForm.active_start_time,
            active_end_time: editForm.active_end_time,
        }
        if (resetForViewChange) patch.growth_baseline_reset_at = nowIso()
        if (await updateSelected(patch)) {
            setShowEdit(false)
            setResetForViewChange(false)
            if (selectedId) await refreshVision(selectedId)
        }
    }

    const archiveSelected = async () => {
        if (!selected || !user.accessToken) return
        const confirmed = window.confirm(
            `Remove "${selected.name}" from active Plant Vision?\n\nCapture and CV will stop for this camera. Historical CameraImage and LeafyCV analysis records will be preserved.`,
        )
        if (!confirmed) return

        setSaving(true)
        const result = await patchCamera(user.accessToken, selected.id, {
            is_archived: true,
            enabled: false,
            cv_enabled: false,
        })
        setSaving(false)
        if (!result.success) {
            setPageError(result.msg)
            return
        }

        const remaining = cameras.filter(camera => camera.id !== selected.id)
        setCameras(remaining)
        setSelectedId(remaining[0]?.id ?? null)
        setLatestImage(null)
        setLatestAnalysis(null)
        setShowEdit(false)
        setPageError("")
    }

    const pointFromEvent = (event: PointerEvent<HTMLDivElement>) => {
        const image = imageRef.current
        if (!image) return null
        const rect = image.getBoundingClientRect()
        if (rect.width <= 0 || rect.height <= 0) return null
        return {
            x: clamp((event.clientX - rect.left) / rect.width),
            y: clamp((event.clientY - rect.top) / rect.height),
        }
    }

    const startRoi = (event: PointerEvent<HTMLDivElement>) => {
        if (!latestImage) return
        const point = pointFromEvent(event)
        if (!point) return
        event.currentTarget.setPointerCapture(event.pointerId)
        setDragStart(point)
        setDraftRoi({ x: point.x, y: point.y, width: 0.001, height: 0.001 })
    }

    const moveRoi = (event: PointerEvent<HTMLDivElement>) => {
        if (!dragStart) return
        const point = pointFromEvent(event)
        if (!point) return
        const x = Math.min(dragStart.x, point.x)
        const y = Math.min(dragStart.y, point.y)
        const width = Math.max(0.001, Math.abs(point.x - dragStart.x))
        const height = Math.max(0.001, Math.abs(point.y - dragStart.y))
        setDraftRoi({ x, y, width: Math.min(width, 1 - x), height: Math.min(height, 1 - y) })
    }

    const endRoi = () => setDragStart(null)

    const saveRoi = async () => {
        if (!draftRoi) return
        // A material ROI change changes the measurement denominator. Reset the
        // temporal boundary in the same PATCH so old/new growth is never compared.
        if (await updateSelected({ roi_points: draftRoi, growth_baseline_reset_at: nowIso() })) {
            setDraftRoi(null)
            if (selectedId) await refreshVision(selectedId)
        }
    }

    const clearRoi = async () => {
        if (await updateSelected({ roi_points: null, growth_baseline_reset_at: nowIso() })) {
            setDraftRoi(null)
            if (selectedId) await refreshVision(selectedId)
        }
    }

    const resetBaseline = async () => {
        if (!window.confirm("Start a new growth baseline? Historical images/analyses are kept; the next valid image becomes the new comparison baseline.")) return
        await updateSelected({ growth_baseline_reset_at: nowIso() })
    }

    const displayRoi = draftRoi || selected?.roi_points || null
    const exactAnalysis = Boolean(latestImage && latestAnalysis && latestImage.image_id === latestAnalysis.image_id)
    const activeHours = selected?.active_start_time && selected.active_end_time
        ? `${formatTime12(selected.active_start_time)} – ${formatTime12(selected.active_end_time)}`
        : "24 hours"

    return (
        <div className="flex flex-col w-full items-center p-5 max-w-300 m-auto gap-5">
            <PageTitlePanel title="Plant Vision" icon={<PiPlant />} refresh={true} />
            {pageError && <div className="w-full border border-high text-high rounded-lg p-3 text-sm">{pageError}</div>}

            <Panel styles="w-full p-4 flex flex-col gap-4">
                <div className="flex flex-wrap gap-3 items-center justify-between">
                    <IconTitle title="Camera / Growth Area" icon={<PiPlant />} />
                    <div className="flex gap-2">
                        <button onClick={loadCameras} className="border border-border rounded-md px-3 py-1 text-xs text-subtext1">Refresh</button>
                        <button onClick={() => setShowCreate(value => !value)} className="border border-highlight text-highlight rounded-md px-3 py-1 text-xs">{showCreate ? "Close" : "Add Camera"}</button>
                    </div>
                </div>

                {showCreate && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 bg-panel2 border border-border rounded-lg p-3">
                        <CameraSettingsFields value={form} onChange={setForm} farmLevels={farmLevels} />
                        <div className="md:col-span-2 flex justify-end">
                            <button disabled={saving} onClick={createNewCamera} className="border border-highlight text-highlight rounded-md px-4 py-2 text-sm disabled:opacity-50">{saving ? "Saving…" : "Create Camera"}</button>
                        </div>
                    </div>
                )}

                {loading ? <p className="text-sm text-subtext2">Loading cameras…</p> : cameras.length === 0 ? (
                    <p className="text-sm text-subtext2">No active camera configured. Add a camera to start Plant Vision.</p>
                ) : (
                    <select value={selectedId || ""} onChange={event => setSelectedId(Number(event.target.value))} className="bg-panel2 border border-border rounded-md p-2 text-subtext1 max-w-xl">
                        {cameras.map(camera => <option key={camera.id} value={camera.id}>{camera.name} — {camera.source_type} — {camera.position || "no position"}</option>)}
                    </select>
                )}
            </Panel>

            {selected && (
                <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1.7fr)_minmax(340px,0.9fr)] gap-5 w-full items-start">
                    <Panel styles="p-4 flex flex-col gap-3 min-w-0">
                        <div className="flex items-center justify-between gap-2 flex-wrap">
                            <div>
                                <p className="text-title font-semibold">Official Camera Image</p>
                                <p className="text-xs text-subtext3">Camera uploads the full frame. Drag over the image to choose the plant group LeafyCV should measure.</p>
                            </div>
                            <div className="flex gap-2">
                                <button disabled={!draftRoi || saving} onClick={saveRoi} className="border border-highlight text-highlight rounded px-2 py-1 text-xs disabled:opacity-40">Save ROI + New Baseline</button>
                                <button disabled={saving} onClick={clearRoi} className="border border-border text-subtext2 rounded px-2 py-1 text-xs disabled:opacity-40">Whole Frame</button>
                            </div>
                        </div>
                        {!latestImage ? (
                            <div className="min-h-64 grid place-items-center border border-dashed border-border rounded-lg text-subtext2 text-sm">Waiting for the Camera service to upload its first official JPEG.</div>
                        ) : (
                            <div
                                className="relative w-full select-none touch-none cursor-crosshair"
                                onPointerDown={startRoi}
                                onPointerMove={moveRoi}
                                onPointerUp={endRoi}
                                onPointerCancel={endRoi}
                            >
                                <img ref={imageRef} src={absoluteImageUrl(latestImage.image_url)} alt={`Official canopy image for ${selected.name}`} className="w-full max-h-[620px] object-contain rounded-lg border border-border block bg-panel2" draggable={false} />
                                {displayRoi && <div className="absolute border-2 border-highlight bg-black/10 pointer-events-none" style={{ left: `${displayRoi.x * 100}%`, top: `${displayRoi.y * 100}%`, width: `${displayRoi.width * 100}%`, height: `${displayRoi.height * 100}%` }} />}
                            </div>
                        )}
                        {latestImage && <p className="text-xs text-subtext3">Image #{latestImage.image_id} captured {formatDateTimeEnglish(latestImage.captured_at)}</p>}
                    </Panel>

                    <div className="flex flex-col gap-5 min-w-0">
                        <Panel styles="p-4 flex flex-col gap-3">
                            <div className="flex items-center justify-between gap-2">
                                <p className="text-title font-semibold">Camera Control</p>
                                <button
                                    disabled={saving}
                                    onClick={() => {
                                        setEditForm(cameraToInput(selected))
                                        setResetForViewChange(false)
                                        setShowEdit(value => !value)
                                    }}
                                    className="border border-border rounded px-2 py-1 text-xs text-subtext1"
                                >
                                    {showEdit ? "Close Settings" : "Edit Settings"}
                                </button>
                            </div>

                            <p className="text-sm text-subtext2">Capture every {selected.capture_interval_minutes} {selected.capture_interval_minutes === 1 ? "minute" : "minutes"} · Active {activeHours}</p>
                            <p className="text-sm text-subtext2">ROI: {selected.roi_points ? "Growth Area rectangle" : "Whole frame"}</p>

                            {showEdit && (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-3 bg-panel2 border border-border rounded-lg p-3">
                                    <CameraSettingsFields value={editForm} onChange={setEditForm} farmLevels={farmLevels} />
                                    <label className="md:col-span-2 lg:col-span-1 xl:col-span-2 flex items-start gap-2 text-xs text-subtext2 border border-border rounded p-2 bg-panel1">
                                        <input type="checkbox" checked={resetForViewChange} onChange={event => setResetForViewChange(event.target.checked)} className="mt-0.5" />
                                        <span><strong className="text-subtext1">Camera view/framing changed materially.</strong><br />Reset the growth baseline when the camera was moved, replaced, tilted, zoomed, or otherwise changed enough that the new image should not be compared with the old view.</span>
                                    </label>
                                    <div className="md:col-span-2 lg:col-span-1 xl:col-span-2 flex justify-end gap-2">
                                        <button disabled={saving} onClick={() => setShowEdit(false)} className="border border-border rounded px-3 py-1.5 text-xs text-subtext1">Cancel</button>
                                        <button disabled={saving} onClick={saveCameraSettings} className="border border-highlight text-highlight rounded px-3 py-1.5 text-xs disabled:opacity-50">Save Settings</button>
                                    </div>
                                </div>
                            )}

                            <div className="flex gap-2 flex-wrap">
                                <button disabled={saving} onClick={() => updateSelected({ enabled: !selected.enabled })} className="border border-border rounded px-2 py-1 text-xs text-subtext1">Camera {selected.enabled ? "Disable" : "Enable"}</button>
                                <button disabled={saving} onClick={() => updateSelected({ cv_enabled: !selected.cv_enabled })} className="border border-border rounded px-2 py-1 text-xs text-subtext1">CV {selected.cv_enabled ? "Disable" : "Enable"}</button>
                                <button disabled={saving} onClick={resetBaseline} className="border border-highlight text-highlight rounded px-2 py-1 text-xs">Reset Growth Baseline</button>
                                <button disabled={saving} onClick={archiveSelected} className="border border-high text-high rounded px-2 py-1 text-xs">Remove Camera</button>
                            </div>
                            <p className="text-xs text-subtext3">Reset the baseline after plants are added/removed/replaced/transferred, the camera view changes materially, or the ROI geometry changes materially. Remove Camera archives it: capture/CV stop, but historical images and analyses are preserved.</p>
                        </Panel>

                        <Panel styles="p-4 flex flex-col gap-4">
                            <div className="flex items-center justify-between gap-2">
                                <p className="text-title font-semibold">LeafyCV Result</p>
                                <button onClick={() => selectedId && refreshVision(selectedId)} className="border border-border rounded px-2 py-1 text-xs text-subtext1">Refresh</button>
                            </div>

                            {!latestAnalysis ? (
                                <p className="text-sm text-subtext2">No analysis yet. LeafyCV will process the newest official image.</p>
                            ) : latestImage && !exactAnalysis ? (
                                <div className="border border-border rounded-md p-3 text-sm text-subtext2">
                                    Analysis pending for newest Image #{latestImage.image_id}. Older Image #{latestAnalysis.image_id} metrics are intentionally not shown here, so an old analysis is never paired with a newer camera image.
                                </div>
                            ) : (
                                <>
                                    <div className="grid grid-cols-2 gap-2">
                                        <div className="bg-panel2 border border-border rounded p-3"><p className="text-xs text-subtext3">Canopy</p><p className="text-title">{metric(latestAnalysis.analysis.total_canopy_coverage)}</p></div>
                                        <div className="bg-panel2 border border-border rounded p-3"><p className="text-xs text-subtext3">Growth change</p><p className="text-title">{metric(latestAnalysis.analysis.growth_change)}</p></div>
                                        <div className="bg-panel2 border border-border rounded p-3"><p className="text-xs text-subtext3">Crowding indicator</p><p className="text-title">{metric(latestAnalysis.analysis.crowding_percentage)}</p></div>
                                        <div className="bg-panel2 border border-border rounded p-3"><p className="text-xs text-subtext3">Green</p><p className="text-title">{metric(latestAnalysis.analysis.green_percentage)}</p></div>
                                        <div className="bg-panel2 border border-border rounded p-3 col-span-2"><p className="text-xs text-subtext3">Yellow</p><p className="text-title">{metric(latestAnalysis.analysis.yellow_percentage)}</p></div>
                                    </div>
                                    <div className={`border rounded-md p-3 text-sm ${latestAnalysis.analysis.measurement_valid ? "border-border text-subtext1" : "border-high text-high"}`}>
                                        Quality: {latestAnalysis.analysis.quality_status} · Measurement {latestAnalysis.analysis.measurement_valid ? "valid" : "rejected"}
                                        {latestAnalysis.analysis.quality_flags.length > 0 && <> · {latestAnalysis.analysis.quality_flags.join(", ")}</>}
                                        {latestAnalysis.analysis.quality_message && <p className="text-xs mt-1">{latestAnalysis.analysis.quality_message}</p>}
                                    </div>
                                </>
                            )}
                        </Panel>
                    </div>
                </div>
            )}
        </div>
    )
}
