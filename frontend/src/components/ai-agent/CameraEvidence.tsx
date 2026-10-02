import { downloadMedia, mediaUrl } from "../../util/constants"
import { Util } from "../../util/Util"
import type { ImageObservation, SourceImage, VisualEvidence } from "../../util/types"
import Badge from "./Badge"

interface Props {
    evidence: VisualEvidence[]
    sourceImages: SourceImage[]
    observations: ImageObservation[]
}

function imageUrl(evidence: VisualEvidence, sourceImages: SourceImage[]) {
    const source = sourceImages.find(image => image.id === evidence.image_id)
    return mediaUrl(source?.url)
}

function observationCameraName(
    observation: ImageObservation,
    evidence: VisualEvidence[],
    sourceImages: SourceImage[],
) {
    if (observation.camera_name?.trim()) return observation.camera_name
    const source = sourceImages.find(image => image.camera_id === observation.camera_id)
    if (source?.camera_name) return source.camera_name
    const visual = evidence.find(item => item.camera_id === observation.camera_id)
    if (visual?.camera_name) return visual.camera_name
    return observation.camera_id != null ? `Camera ${observation.camera_id}` : "Camera"
}

export default function CameraEvidence({ evidence, sourceImages, observations }: Props) {
    if (evidence.length === 0 && sourceImages.length === 0 && observations.length === 0) {
        return <p className="text-sm text-subtext3">No camera evidence for this run.</p>
    }

    return (
        <div className="flex flex-col gap-3">
            <div className="grid gap-3 sm:grid-cols-2">
                {evidence.map(item => {
                    const url = imageUrl(item, sourceImages)
                    return (
                        <div key={item.image_id} className="border border-border rounded-lg bg-panel2 overflow-hidden">
                            {url ?
                                <img
                                    src={url}
                                    alt={`${item.camera_name} camera frame`}
                                    className="w-full h-36 object-cover bg-panel3 hover:cursor-pointer"
                                    onClick={() => { void downloadMedia(url) }}
                                />
                            : null}
                            <div className="p-3 flex flex-col gap-2">
                                <div className="flex flex-wrap items-center gap-2">
                                    <p className="text-sm text-subtext1 font-semibold">{item.camera_name}</p>
                                    <Badge label={item.quality_status} />
                                    <Badge label={item.selected ? "Selected" : "Rejected"} />
                                </div>
                                <p className="text-xs text-subtext3">
                                    {Util.formatDateTime(new Date(item.captured_at))}
                                </p>
                                <p className="text-xs text-subtext2">{item.reason}</p>
                            </div>
                        </div>
                    )
                })}
            </div>
            {observations.length > 0 ?
                <div className="flex flex-col gap-2">
                    <p className="text-sm text-subtext1 font-semibold">VLM observations</p>
                    {observations.map((item, index) => (
                        <p key={`${item.camera_id ?? "obs"}-${index}`} className="text-xs text-subtext2">
                            {`${observationCameraName(item, evidence, sourceImages)}: `}
                            {String(item.observation ?? JSON.stringify(item))}
                        </p>
                    ))}
                </div>
            : null}
        </div>
    )
}
