import {
    API_ROUTES,
    aiFarmSettingsUrl,
    aiGenerateUrl,
    aiLatestUrl,
    aiProviderTestUrl,
    aiRecentUrl,
    cameraCaptureUrl,
    cameraImagesUrl,
    deviceStateUrl,
    farmCamerasUrl,
    farmDashboardUrl,
    farmLevelsUrl,
    farmStateUrl,
    recommendationDetailUrl,
    recommendationHistoryUrl,
    sensorHistoryUrl,
    sensorIngestUrl,
    sensorReadingsUrl,
    withQuery,
} from "./constants";
import type {
    AIConfiguration,
    AIConfigurationPatch,
    APIResult,
    BABatch,
    BatchDefinition,
    CameraImage,
    CameraWrite,
    DeviceStateResult,
    Farm,
    FarmCamera,
    FarmDashboard,
    FarmLevel,
    FarmState,
    GaDefinition,
    GAGrowingArea,
    GalleryImage,
    MagentaState,
    MoveBatch,
    Page,
    PowerboardDevice,
    ProviderTestResult,
    ProviderTestRole,
    RecommendationRun,
    SensorCollectionResult,
    SensorHistory,
    SensorIngestConfiguration,
    SensorIngestPatch,
    SensorReadingRecord,
} from "./types";

function errorMessage(body: unknown, fallback: string) {
    if (!body || typeof body !== "object") return fallback
    const record = body as Record<string, unknown>
    const detail = record.detail ?? record.message ?? record.error ?? record.msg
    if (typeof detail === "string" && detail.trim()) return detail
    if (Array.isArray(detail)) return detail.map(String).join(", ")
    const fieldErrors: string[] = []
    for (const [key, value] of Object.entries(record)) {
        if (key === "run" || key === "success") continue
        if (Array.isArray(value)) fieldErrors.push(`${key}: ${value.map(String).join(", ")}`)
        else if (typeof value === "string" && value.trim() && key !== "detail" && key !== "message" && key !== "error" && key !== "msg") {
            fieldErrors.push(`${key}: ${value}`)
        }
    }
    if (fieldErrors.length) return fieldErrors.join(" ")
    return fallback
}

type ApiRequestOptions = RequestInit & { emptyOnStatus?: number[] }

async function apiRequest<T>(url: string, accessToken?: string, options: ApiRequestOptions = {}): Promise<APIResult<T>> {
    const { emptyOnStatus, headers, ...rest } = options
    let data: T | undefined;
    try {
        const res = await fetch(url, {
            ...rest,
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${accessToken}`,
                ...headers,
            },
        });
        const raw = await res.text();
        let parsed: unknown = undefined;
        if (raw) {
            try {
                parsed = JSON.parse(raw);
            } catch {
                parsed = undefined;
            }
        }
        data = parsed as T;

        if (emptyOnStatus?.includes(res.status)) {
            return { success: true, msg: "", data: undefined }
        }

        if (!res.ok) {
            return {
                success: false,
                msg: errorMessage(parsed, res.status === 409 ? "This action is already running." : `Request failed (${res.status})`),
                data,
            };
        }

        return { success: true, msg: "", data };
    } catch (error) {
        return { success: false, msg: (error as Error).message, data };
    }
}

export async function getGrowingAreas(accessToken: string | undefined, farmId: number): Promise<APIResult<GAGrowingArea[]>>{
    return await apiRequest<GAGrowingArea[]>(withQuery(API_ROUTES.getGrowingAreas, { farm_id: farmId }), accessToken, {
        method: "GET"
    })
}

export async function getBatches(accessToken: string | undefined, farmId: number): Promise<APIResult<BABatch[]>>{
    return await apiRequest<BABatch[]>(withQuery(API_ROUTES.getBatches, { farm_id: farmId }), accessToken, {
        method: "GET"
    })
}

export async function moveBatch(accessToken: string | undefined, farmId: number, moveDetails: MoveBatch): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.moveBatch, accessToken, {
        method: "PATCH",
        body: JSON.stringify({ ...moveDetails, farm_id: farmId }),
        headers: {"Content-Type": "application/json",}
    })
}

export async function createGrowingArea(accessToken: string | undefined, farmId: number, gaDetails: GaDefinition): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.createGrowingArea, accessToken, {
        method: "POST",
        body: JSON.stringify({ ...gaDetails, farm_id: farmId }),
        headers: {"Content-Type": "application/json",}
    })
}

export async function updateGrowingArea(accessToken: string | undefined, farmId: number, gaDetails: GaDefinition): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.updateGrowingAreas, accessToken, {
        method: "PATCH",
        body: JSON.stringify({ ...gaDetails, farm_id: farmId }),
        headers: {"Content-Type": "application/json",}
    })
}

export async function updateBatch(accessToken: string | undefined, farmId: number, details: {batchID: string, action: "harvest" | "terminate"}): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.updateBatch, accessToken, {
        method: "PATCH",
        body: JSON.stringify({ ...details, farm_id: farmId }),
        headers: {"Content-Type": "application/json",}
    })
}

export async function createBatch(accessToken: string | undefined, farmId: number, details: BatchDefinition): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.createBatch, accessToken, {
        method: "POST",
        body: JSON.stringify({ ...details, farm_id: farmId }),
        headers: {"Content-Type": "application/json",}
    })
}

export async function deleteGrowingArea(accessToken: string | undefined, farmId: number, GaId: string): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.deleteGrowingArea, accessToken, {
        method: "DELETE",
        body: JSON.stringify({ growingAreaID: GaId, farm_id: farmId }),
        headers: {"Content-Type": "application/json",}
    })
}

export async function createFarmWithLayout(
    accessToken: string | undefined,
    name: string,
    location: string,
): Promise<APIResult<Farm>> {
    return await apiRequest<Farm>(API_ROUTES.getFarms, accessToken, {
        method: "POST",
        body: JSON.stringify({ name, location }),
    })
}

export async function getFarms(accessToken: string | undefined): Promise<APIResult<Page<Farm>>> {
    return await apiRequest<Page<Farm>>(withQuery(API_ROUTES.getFarms, { limit: 500 }), accessToken, {
        method: "GET",
    })
}

export async function deleteFarm(accessToken: string | undefined, farmId: number): Promise<APIResult<undefined>> {
    return await apiRequest<undefined>(`${API_ROUTES.getFarms}${farmId}/`, accessToken, {
        method: "DELETE",
    })
}

export async function getFarmDashboard(accessToken: string | undefined, farmId: number): Promise<APIResult<FarmDashboard>> {
    return await apiRequest<FarmDashboard>(farmDashboardUrl(farmId), accessToken, {
        method: "GET",
    })
}

export async function getSensorIngest(accessToken: string | undefined, farmId: number): Promise<APIResult<Page<SensorIngestConfiguration>>> {
    return await apiRequest<Page<SensorIngestConfiguration>>(withQuery(sensorIngestUrl(farmId), { limit: 500 }), accessToken, {
        method: "GET",
    })
}

export async function patchSensorIngest(
    accessToken: string | undefined,
    farmId: number,
    deviceId: number,
    patch: SensorIngestPatch,
): Promise<APIResult<SensorIngestConfiguration>> {
    return await apiRequest<SensorIngestConfiguration>(sensorIngestUrl(farmId, deviceId), accessToken, {
        method: "PATCH",
        body: JSON.stringify(patch),
    })
}

export async function testSensorIngest(
    accessToken: string | undefined,
    farmId: number,
    deviceId: number,
): Promise<APIResult<SensorCollectionResult>> {
    return await apiRequest<SensorCollectionResult>(`${sensorIngestUrl(farmId, deviceId)}test/`, accessToken, {
        method: "POST",
        body: JSON.stringify({}),
    })
}

export async function collectSensorIngest(
    accessToken: string | undefined,
    farmId: number,
    deviceId: number,
): Promise<APIResult<SensorCollectionResult>> {
    return await apiRequest<SensorCollectionResult>(`${sensorIngestUrl(farmId, deviceId)}collect/`, accessToken, {
        method: "POST",
        body: JSON.stringify({}),
    })
}

export async function getSensorReadings(
    accessToken: string | undefined,
    farmId: number,
    query: { sensors?: string; quality?: string; start?: string; end?: string; limit?: number; offset?: number },
): Promise<APIResult<Page<SensorReadingRecord>>> {
    return await apiRequest<Page<SensorReadingRecord>>(withQuery(sensorReadingsUrl(farmId), query), accessToken, {
        method: "GET",
    })
}

export async function getSensorHistory(
    accessToken: string | undefined,
    farmId: number,
    query: { preset?: string; start?: string; end?: string; sensors?: string; bucket?: string; limit?: number },
): Promise<APIResult<SensorHistory>> {
    return await apiRequest<SensorHistory>(withQuery(sensorHistoryUrl(farmId), query), accessToken, {
        method: "GET",
    })
}

export async function getFarmCameras(accessToken: string | undefined, farmId: number): Promise<APIResult<Page<FarmCamera>>> {
    return await apiRequest<Page<FarmCamera>>(withQuery(farmCamerasUrl(farmId), { limit: 500 }), accessToken, {
        method: "GET",
    })
}

export async function createFarmCamera(
    accessToken: string | undefined,
    farmId: number,
    body: CameraWrite,
): Promise<APIResult<FarmCamera>> {
    return await apiRequest<FarmCamera>(farmCamerasUrl(farmId), accessToken, {
        method: "POST",
        body: JSON.stringify(body),
    })
}

export async function patchFarmCamera(
    accessToken: string | undefined,
    farmId: number,
    cameraId: number,
    patch: Partial<CameraWrite> & { is_archived?: boolean },
): Promise<APIResult<FarmCamera>> {
    return await apiRequest<FarmCamera>(farmCamerasUrl(farmId, cameraId), accessToken, {
        method: "PATCH",
        body: JSON.stringify(patch),
    })
}

export async function captureFarmCamera(
    accessToken: string | undefined,
    farmId: number,
    cameraId: number,
): Promise<APIResult<CameraImage>> {
    return await apiRequest<CameraImage>(cameraCaptureUrl(farmId, cameraId), accessToken, {
        method: "POST",
        body: JSON.stringify({}),
    })
}

export async function getCameraImages(
    accessToken: string | undefined,
    farmId: number,
    query: {
        cameras?: string
        start?: string
        end?: string
        quality?: string
        vlm_ready?: boolean
        ai_used?: boolean
        limit?: number
        offset?: number
    },
): Promise<APIResult<Page<GalleryImage>>> {
    return await apiRequest<Page<GalleryImage>>(withQuery(cameraImagesUrl(farmId), query), accessToken, {
        method: "GET",
    })
}

export async function getFarmLevels(accessToken: string | undefined): Promise<APIResult<FarmLevel[]>> {
    return await apiRequest<FarmLevel[]>(farmLevelsUrl(), accessToken, {
        method: "GET",
    })
}

export async function getRecommendationHistory(
    accessToken: string | undefined,
    farmId: number,
    query: { status?: string; trigger?: string; input_mode?: string; start?: string; end?: string; limit?: number; offset?: number },
): Promise<APIResult<Page<RecommendationRun>>> {
    return await apiRequest<Page<RecommendationRun>>(withQuery(recommendationHistoryUrl(farmId), query), accessToken, {
        method: "GET",
    })
}

export async function getRecommendationDetail(
    accessToken: string | undefined,
    farmId: number,
    runId: number,
): Promise<APIResult<RecommendationRun>> {
    return await apiRequest<RecommendationRun>(recommendationDetailUrl(farmId, runId), accessToken, {
        method: "GET",
    })
}

export async function getFarmState(accessToken: string | undefined, farmId: number): Promise<APIResult<FarmState>> {
    return await apiRequest<FarmState>(farmStateUrl(farmId), accessToken, {
        method: "GET",
    })
}

export async function getDevices(accessToken: string | undefined): Promise<APIResult<PowerboardDevice[]>> {
    return await apiRequest<PowerboardDevice[]>(API_ROUTES.getDevices, accessToken, {
        method: "GET",
    })
}

export async function setDeviceState(
    accessToken: string | undefined,
    deviceId: number,
    state: "ON" | "OFF",
): Promise<APIResult<DeviceStateResult>> {
    return await apiRequest<DeviceStateResult>(deviceStateUrl(deviceId), accessToken, {
        method: "POST",
        body: JSON.stringify({ state }),
    })
}

export async function getMagentaState(accessToken: string | undefined): Promise<APIResult<MagentaState>> {
    return await apiRequest<MagentaState>(API_ROUTES.magentaState, accessToken, {
        method: "GET",
    })
}

export async function setMagentaState(
    accessToken: string | undefined,
    state: "ON" | "OFF",
): Promise<APIResult<MagentaState>> {
    return await apiRequest<MagentaState>(API_ROUTES.magentaState, accessToken, {
        method: "POST",
        body: JSON.stringify({ state }),
    })
}

export async function getAiFarmSettings(
    accessToken: string | undefined,
    farmId: number,
): Promise<APIResult<AIConfiguration>> {
    return await apiRequest<AIConfiguration>(aiFarmSettingsUrl(farmId), accessToken, {
        method: "GET",
    })
}

export async function patchAiFarmSettings(
    accessToken: string | undefined,
    farmId: number,
    patch: AIConfigurationPatch,
): Promise<APIResult<AIConfiguration>> {
    return await apiRequest<AIConfiguration>(aiFarmSettingsUrl(farmId), accessToken, {
        method: "PATCH",
        body: JSON.stringify(patch),
    })
}

export async function testAiProvider(
    accessToken: string | undefined,
    farmId: number,
    role: ProviderTestRole,
): Promise<APIResult<ProviderTestResult>> {
    return await apiRequest<ProviderTestResult>(aiProviderTestUrl(farmId), accessToken, {
        method: "POST",
        body: JSON.stringify({ role }),
    })
}

export async function generateFarmRecommendations(
    accessToken: string | undefined,
    farmId: number,
    deviceId?: number,
): Promise<APIResult<RecommendationRun>> {
    const body: { device_id?: number } = {}
    if (deviceId != null) body.device_id = deviceId
    const result = await apiRequest<RecommendationRun | { error?: string; run?: RecommendationRun }>(
        aiGenerateUrl(farmId),
        accessToken,
        {
            method: "POST",
            body: JSON.stringify(body),
        },
    )
    if (result.success) {
        const payload = result.data
        if (payload && "id" in payload && "recommendations" in payload) {
            return { success: true, msg: "", data: payload as RecommendationRun }
        }
    }
    const payload = result.data as { error?: string; run?: RecommendationRun } | undefined
    return {
        success: false,
        msg: result.msg,
        data: payload?.run,
    }
}

export async function getLatestRecommendations(
    accessToken: string | undefined,
    farmId: number,
): Promise<APIResult<RecommendationRun | null>> {
    const result = await apiRequest<RecommendationRun>(aiLatestUrl(farmId), accessToken, {
        method: "GET",
        emptyOnStatus: [404],
    })
    if (!result.success) return { success: false, msg: result.msg, data: result.data }
    return { success: true, msg: "", data: result.data ?? null }
}

export async function getRecentRecommendations(
    accessToken: string | undefined,
    farmId: number,
): Promise<APIResult<RecommendationRun[]>> {
    return await apiRequest<RecommendationRun[]>(aiRecentUrl(farmId), accessToken, {
        method: "GET",
    })
}
