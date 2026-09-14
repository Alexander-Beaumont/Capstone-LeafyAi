import { API_ROUTES, BACKEND_BASEURL, POWERBOARD_BASEURL } from "./constants"
import type {
    APIResult,
    BABatch,
    BatchDefinition,
    Camera,
    CameraInput,
    FarmLevel,
    GaDefinition,
    GAGrowingArea,
    LatestAnalysis,
    LatestImage,
    MoveBatch,
    PowerDevice,
    Sensor,
    SensorReading,
} from "./types"

async function parseBody(res: Response): Promise<unknown> {
    if (res.status === 204) return undefined
    const text = await res.text()
    if (!text) return undefined
    try { return JSON.parse(text) } catch { return text }
}

async function apiRequest<T>(url: string, accessToken?: string, options: RequestInit = {}): Promise<APIResult<T>> {
    try {
        const headers = new Headers(options.headers || {})
        if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`)
        if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json")
        headers.set("Accept", "application/json")

        const res = await fetch(url, { ...options, headers })
        const body = await parseBody(res)
        if (!res.ok) {
            const flattenError = (value: unknown): string[] => {
                if (typeof value === "string") return [value]
                if (Array.isArray(value)) return value.flatMap(flattenError)
                if (value && typeof value === "object") {
                    return Object.entries(value as Record<string, unknown>).flatMap(([key, child]) =>
                        flattenError(child).map(message => `${key}: ${message}`)
                    )
                }
                return []
            }
            const messages = flattenError(body)
            const msg = messages.length > 0 ? messages.join(" · ") : `Request failed (${res.status})`
            return { success: false, msg, data: body as T, status: res.status }
        }
        return { success: true, msg: "", data: body as T, status: res.status }
    } catch (error) {
        return { success: false, msg: (error as Error).message }
    }
}

export async function getGrowingAreas(token?: string) { return apiRequest<GAGrowingArea[]>(API_ROUTES.getGrowingAreas, token) }
export async function getBatches(token?: string) { return apiRequest<BABatch[]>(API_ROUTES.getBatches, token) }
export async function moveBatch(token: string | undefined, details: MoveBatch) { return apiRequest<{success: boolean; msg: string}>(API_ROUTES.moveBatch, token, {method: "PATCH", body: JSON.stringify(details)}) }
export async function createGrowingArea(token: string | undefined, details: GaDefinition) { return apiRequest<{success: boolean; msg: string}>(API_ROUTES.createGrowingArea, token, {method: "POST", body: JSON.stringify(details)}) }
export async function updateGrowingArea(token: string | undefined, details: GaDefinition) { return apiRequest<{success: boolean; msg: string}>(API_ROUTES.updateGrowingAreas, token, {method: "PATCH", body: JSON.stringify(details)}) }
export async function updateBatch(token: string | undefined, details: {batchID: string; action: "harvest" | "terminate"}) { return apiRequest<{success: boolean; msg: string}>(API_ROUTES.updateBatch, token, {method: "PATCH", body: JSON.stringify(details)}) }
export async function createBatch(token: string | undefined, details: BatchDefinition) { return apiRequest<{success: boolean; msg: string}>(API_ROUTES.createBatch, token, {method: "POST", body: JSON.stringify(details)}) }
export async function deleteGrowingArea(token: string | undefined, gaId: string) { return apiRequest<{success: boolean; msg: string}>(API_ROUTES.deleteGrowingArea, token, {method: "DELETE", body: JSON.stringify({growingAreaID: gaId})}) }

export async function getCameras(token?: string) { return apiRequest<Camera[]>(API_ROUTES.cameras, token) }
export async function getFarmLevels(token?: string) { return apiRequest<FarmLevel[]>(API_ROUTES.farmLevels, token) }
export async function createCamera(token: string | undefined, camera: CameraInput) { return apiRequest<Camera>(API_ROUTES.cameras, token, {method: "POST", body: JSON.stringify(camera)}) }
export async function patchCamera(token: string | undefined, cameraId: number, patch: Partial<CameraInput>) { return apiRequest<Camera>(`${API_ROUTES.cameras}${cameraId}/`, token, {method: "PATCH", body: JSON.stringify(patch)}) }
export async function getLatestImage(token: string | undefined, cameraId: number) { return apiRequest<LatestImage>(`${BACKEND_BASEURL}/api/cv/cameras/${cameraId}/latest-image/`, token) }
export async function getLatestAnalysis(token: string | undefined, cameraId: number) { return apiRequest<LatestAnalysis>(`${BACKEND_BASEURL}/api/cv/cameras/${cameraId}/latest-analysis/`, token) }

export async function getSensors(token?: string) { return apiRequest<Sensor[]>(API_ROUTES.sensors, token) }
export async function getSensorReadings(token?: string) { return apiRequest<SensorReading[]>(`${API_ROUTES.sensorReadings}?limit=200`, token) }

export async function getPowerDevices() { return apiRequest<PowerDevice[]>(API_ROUTES.powerDevices) }
export async function setPowerDeviceState(deviceId: number, state: "ON" | "OFF") {
    return apiRequest<PowerDevice>(`${POWERBOARD_BASEURL}/api/devices/${deviceId}/state/`, undefined, {method: "POST", body: JSON.stringify({state})})
}
