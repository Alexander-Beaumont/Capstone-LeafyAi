import {
    API_ROUTES,
    aiFarmSettingsUrl,
    aiGenerateUrl,
    aiLatestUrl,
    aiProviderTestUrl,
    aiRecentUrl,
    deviceStateUrl,
    farmStateUrl,
} from "./constants";
import type {
    AIConfiguration,
    AIConfigurationPatch,
    APIResult,
    BABatch,
    BatchDefinition,
    DeviceStateResult,
    Farm,
    FarmState,
    GaDefinition,
    GAGrowingArea,
    MagentaState,
    MoveBatch,
    PowerboardDevice,
    ProviderTestResult,
    ProviderTestRole,
    RecommendationRun,
} from "./types";

function errorMessage(body: unknown, fallback: string) {
    if (!body || typeof body !== "object") return fallback
    const record = body as Record<string, unknown>
    const detail = record.detail ?? record.message ?? record.error
    if (typeof detail === "string" && detail.trim()) return detail
    if (Array.isArray(detail)) return detail.map(String).join(", ")
    const fieldErrors: string[] = []
    for (const [key, value] of Object.entries(record)) {
        if (key === "run" || key === "success") continue
        if (Array.isArray(value)) fieldErrors.push(`${key}: ${value.map(String).join(", ")}`)
        else if (typeof value === "string" && value.trim() && key !== "detail" && key !== "message" && key !== "error") {
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
                msg: errorMessage(parsed, `Request failed (${res.status})`),
                data,
            };
        }

        return { success: true, msg: "", data };
    } catch (error) {
        return { success: false, msg: (error as Error).message, data };
    }
}

export async function getGrowingAreas(accessToken?: string): Promise<APIResult<GAGrowingArea[]>>{
    return await apiRequest<GAGrowingArea[]>(API_ROUTES.getGrowingAreas, accessToken, {
        method: "GET"
    })
}

export async function getBatches(accessToken: string | undefined): Promise<APIResult<BABatch[]>>{
    return await apiRequest<BABatch[]>(API_ROUTES.getBatches, accessToken, {
        method: "GET"
    })
}

export async function moveBatch(accessToken: string | undefined, moveDetails: MoveBatch): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.moveBatch, accessToken, {
        method: "PATCH",
        body: JSON.stringify(moveDetails),
        headers: {"Content-Type": "application/json",}
    })
}

export async function createGrowingArea(accessToken: string | undefined, gaDetails: GaDefinition): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.createGrowingArea, accessToken, {
        method: "POST",
        body: JSON.stringify(gaDetails),
        headers: {"Content-Type": "application/json",}
    })
}

export async function updateGrowingArea(accessToken: string | undefined, gaDetails: GaDefinition): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.updateGrowingAreas, accessToken, {
        method: "PATCH",
        body: JSON.stringify(gaDetails),
        headers: {"Content-Type": "application/json",}
    })
}

export async function updateBatch(accessToken: string | undefined, details: {batchID: string, action: "harvest" | "terminate"}): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.updateBatch, accessToken, {
        method: "PATCH",
        body: JSON.stringify(details),
        headers: {"Content-Type": "application/json",}
    })
}

export async function createBatch(accessToken: string | undefined, details: BatchDefinition): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.createBatch, accessToken, {
        method: "POST",
        body: JSON.stringify(details),
        headers: {"Content-Type": "application/json",}
    })
}

export async function deleteGrowingArea(accessToken: string | undefined, GaId: string): Promise<APIResult<{success: boolean, msg: string}>>{
    return await apiRequest<{success: boolean, msg: string}>(API_ROUTES.deleteGrowingArea, accessToken, {
        method: "DELETE",
        body: JSON.stringify({growingAreaID: GaId}),
        headers: {"Content-Type": "application/json",}
    })
}

export async function getFarms(accessToken: string | undefined): Promise<APIResult<Farm[]>> {
    return await apiRequest<Farm[]>(API_ROUTES.getFarms, accessToken, {
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