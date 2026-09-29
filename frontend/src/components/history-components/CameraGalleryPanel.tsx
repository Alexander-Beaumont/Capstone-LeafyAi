import { useContext, useEffect, useState } from "react"
import Panel from "../primatives/Panel"
import IconTitle from "../primatives/IconTitle"
import Dropdown, { type dataFormat } from "../primatives/Dropdown"
import { LuCamera } from "react-icons/lu"
import { FarmOverviewContext } from "../../providers/FarmOverviewProvider"
import { userContext } from "../../providers/UserProvider"
import { getCameraImages, getFarmCameras } from "../../util/api-service-layer"
import { mediaUrl } from "../../util/constants"
import { formatTimestamp, localInputToIso } from "../../util/operator"
import type { FarmCamera, GalleryImage } from "../../util/types"
import Pager from "./Pager"
import DateTimeField from "../primatives/DateTimeField"

const QUALITIES = ["PASS", "WARN", "FAIL", "UNKNOWN"]
const LIMIT = 12
const flags: dataFormat[] = [
    { id: 0, name: "any", data: "" },
    { id: 1, name: "true", data: "true" },
    { id: 2, name: "false", data: "false" },
]

function flagValue(item: dataFormat) {
    if (item.data === "true") return true
    if (item.data === "false") return false
    return undefined
}

export default function CameraGalleryPanel() {
    const user = useContext(userContext)
    const overview = useContext(FarmOverviewContext)
    const [cameras, setCameras] = useState<FarmCamera[]>([])
    const [selected, setSelected] = useState<number[]>([])
    const [qualities, setQualities] = useState<string[]>([])
    const [vlmReady, setVlmReady] = useState(flags[0])
    const [aiUsed, setAiUsed] = useState(flags[0])
    const [start, setStart] = useState("")
    const [end, setEnd] = useState("")
    const [offset, setOffset] = useState(0)
    const [count, setCount] = useState(0)
    const [images, setImages] = useState<GalleryImage[]>([])
    const [error, setError] = useState("")
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        if (!user.accessToken || overview.farmId == null) return
        let cancelled = false
        getFarmCameras(user.accessToken, overview.farmId).then(result => {
            if (cancelled || !result.success) return
            setCameras(result.data?.results ?? [])
        })
        return () => {
            cancelled = true
        }
    }, [user.accessToken, overview.farmId])

    useEffect(() => {
        if (!user.accessToken || overview.farmId == null) return
        let cancelled = false
        const run = async () => {
            setLoading(true)
            const result = await getCameraImages(user.accessToken, overview.farmId!, {
                cameras: selected.join(","),
                quality: qualities.join(","),
                vlm_ready: flagValue(vlmReady),
                ai_used: flagValue(aiUsed),
                start: localInputToIso(start),
                end: localInputToIso(end),
                limit: LIMIT,
                offset,
            })
            if (cancelled) return
            setLoading(false)
            if (!result.success || !result.data) {
                setImages([])
                setCount(0)
                setError(result.msg)
                return
            }
            setError("")
            setImages(result.data.results)
            setCount(result.data.count)
        }
        run()
        return () => {
            cancelled = true
        }
    }, [user.accessToken, overview.farmId, selected, qualities, vlmReady, aiUsed, start, end, offset])

    return (
        <Panel styles="w-full p-3 flex flex-col gap-4">
            <IconTitle title="Camera gallery" icon={<LuCamera size={16} />} />
            {!overview.farmId ?
                <p className="text-sm text-subtext3">Select a farm to load images.</p>
            : <>
                <div className="flex flex-wrap gap-2">
                    {cameras.map(camera => (
                        <button
                            key={camera.id}
                            type="button"
                            className={`text-xs px-2 py-1 rounded-md border ${selected.includes(camera.id) ? "bg-highlight text-btn-text border-highlight" : "bg-panel2 text-subtext2 border-border"}`}
                            onClick={() => {
                                setSelected(current => current.includes(camera.id) ? current.filter(id => id !== camera.id) : [...current, camera.id])
                                setOffset(0)
                            }}
                        >
                            {camera.name}
                        </button>
                    ))}
                </div>
                <div className="flex flex-wrap gap-2">
                    {QUALITIES.map(quality => (
                        <button
                            key={quality}
                            type="button"
                            className={`text-xs px-2 py-1 rounded-md border ${qualities.includes(quality) ? "bg-highlight text-btn-text border-highlight" : "bg-panel2 text-subtext2 border-border"}`}
                            onClick={() => {
                                setQualities(current => current.includes(quality) ? current.filter(item => item !== quality) : [...current, quality])
                                setOffset(0)
                            }}
                        >
                            {quality}
                        </button>
                    ))}
                </div>
                <div className="flex flex-wrap gap-3">
                    <div className="flex flex-col gap-1">
                        <p className="text-xs text-subtext3">VLM ready</p>
                        <Dropdown items={flags} selectedItem={vlmReady} setSelectedItem={id => { setVlmReady(flags[id]); setOffset(0) }} showIcon divStyles="w-28" />
                    </div>
                    <div className="flex flex-col gap-1">
                        <p className="text-xs text-subtext3">Used by AI</p>
                        <Dropdown items={flags} selectedItem={aiUsed} setSelectedItem={id => { setAiUsed(flags[id]); setOffset(0) }} showIcon divStyles="w-28" />
                    </div>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                    <DateTimeField name="Start" value={start} setValue={value => { setStart(value); setOffset(0) }} />
                    <DateTimeField name="End" value={end} setValue={value => { setEnd(value); setOffset(0) }} />
                </div>
                {error ? <p className="text-xs text-high">{error}</p> : null}
                {loading && images.length === 0 ? <div className="h-24 bg-panel2 animate-pulse rounded-md" /> : null}
                {images.length === 0 && !loading ?
                    <p className="text-sm text-subtext3">No images match these filters.</p>
                :
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                        {images.map(image => {
                            const src = mediaUrl(image.path)
                            return (
                                <figure key={image.id} className="border border-border rounded-lg overflow-hidden bg-panel2">
                                    {src ?
                                        <img src={src} alt={`${image.camera_name} capture`} className="w-full h-28 object-cover" />
                                    :
                                        <div className="h-28" />
                                    }
                                    <figcaption className="p-2 flex flex-col gap-1">
                                        <p className="text-xs text-title font-semibold">{image.camera_name}</p>
                                        <p className="text-[11px] text-subtext3">{formatTimestamp(image.captured_at)}</p>
                                        <p className="text-[11px] text-subtext2">{image.quality_status}{image.ai_used ? " · used by AI" : ""}</p>
                                    </figcaption>
                                </figure>
                            )
                        })}
                    </div>
                }
                <Pager offset={offset} limit={LIMIT} count={count} onOffset={setOffset} />
            </>}
        </Panel>
    )
}
