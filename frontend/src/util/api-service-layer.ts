import { API_ROUTES, deviceStateUrl, farmStateUrl } from "./constants";
import type {
    AIDecision,
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
} from "./types";

function errorMessage(body: unknown, fallback: string) {
    if (!body || typeof body !== "object") return fallback
    const record = body as Record<string, unknown>
    const detail = record.detail ?? record.message ?? record.error
    if (typeof detail === "string" && detail.trim()) return detail
    if (Array.isArray(detail)) return detail.map(String).join(", ")
    return fallback
}

async function apiRequest<T>(url: string, accessToken?: string, options: RequestInit = {}): Promise<APIResult<T>> {
    let data: T | undefined;
    try {
        const res = await fetch(url, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${accessToken}`,
                ...options.headers,
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

export async function getAiDecisions(accessToken: string | undefined): Promise<APIResult<AIDecision[]>> {
    return await apiRequest<AIDecision[]>(API_ROUTES.getAiDecisions, accessToken, {
        method: "GET",
    })
}