import type { dataFormat } from "../components/primatives/Dropdown"

export const SMALL_WINDOW_WIDTH = 1000
export const GROWTH_STAGES: dataFormat[] = [
    {name: "seedling", id: 0},
    {name: "early", id: 1},
    {name: "growth", id: 2},
    {name: "mature", id: 3}
]

export const BATCH_STATUS: dataFormat[] = [
    {name: "active", id: 0},
    {name: "harvested", id: 1},
    {name: "failed", id: 2},
]


// Centralise backend route construction so pages/providers do not embed API paths.
export const API_ROUTES = {
    login: `${import.meta.env.VITE_BACKEND_BASEURL}/api/auth/login/`,
    signup: `${import.meta.env.VITE_BACKEND_BASEURL}/api/auth/register/`,
    refresh: `${import.meta.env.VITE_BACKEND_BASEURL}/api/auth/refresh/`,
    getGrowingAreas: `${import.meta.env.VITE_BACKEND_BASEURL}/api/growing-areas`,
    getBatches: `${import.meta.env.VITE_BACKEND_BASEURL}/api/batches`,
    moveBatch: `${import.meta.env.VITE_BACKEND_BASEURL}/api/move-batch`,
    createGrowingArea: `${import.meta.env.VITE_BACKEND_BASEURL}/api/create-growing-area`,
    updateGrowingAreas: `${import.meta.env.VITE_BACKEND_BASEURL}/api/update-growing-area`,
    updateBatch: `${import.meta.env.VITE_BACKEND_BASEURL}/api/update-batch`,
    createBatch: `${import.meta.env.VITE_BACKEND_BASEURL}/api/create-batch`,
    deleteGrowingArea: `${import.meta.env.VITE_BACKEND_BASEURL}/api/delete-growing-area`,
    getFarms: `${import.meta.env.VITE_BACKEND_BASEURL}/api/farms/`,
    getDevices: `${import.meta.env.VITE_BACKEND_BASEURL}/api/devices/`,
    magentaState: `${import.meta.env.VITE_BACKEND_BASEURL}/api/lighting/magenta/state/`,
}

function backendUrl(path: string) {
    const base = String(import.meta.env.VITE_BACKEND_BASEURL ?? "").replace(/\/$/, "")
    return `${base}${path}`
}

export function farmStateUrl(farmId: number) {
    return backendUrl(`/api/farm-state/${farmId}/`)
}

export function farmDashboardUrl(farmId: number) {
    return backendUrl(`/api/farms/${farmId}/dashboard/`)
}

export function sensorIngestUrl(farmId: number, deviceId?: number) {
    const suffix = deviceId == null ? "" : `${deviceId}/`
    return backendUrl(`/api/farms/${farmId}/sensor-ingest/${suffix}`)
}

export function sensorReadingsUrl(farmId: number) {
    return backendUrl(`/api/farms/${farmId}/sensor-readings/`)
}

export function sensorHistoryUrl(farmId: number) {
    return backendUrl(`/api/farms/${farmId}/sensor-history/`)
}

export function farmCamerasUrl(farmId: number, cameraId?: number) {
    const suffix = cameraId == null ? "" : `${cameraId}/`
    return backendUrl(`/api/farms/${farmId}/cameras/${suffix}`)
}

export function cameraCaptureUrl(farmId: number, cameraId: number) {
    return backendUrl(`/api/farms/${farmId}/cameras/${cameraId}/capture/`)
}

export function cameraImagesUrl(farmId: number) {
    return backendUrl(`/api/farms/${farmId}/camera-images/`)
}

export function recommendationHistoryUrl(farmId: number) {
    return backendUrl(`/api/ai-agent/farms/${farmId}/recommendations/history/`)
}

export function recommendationDetailUrl(farmId: number, runId: number) {
    return backendUrl(`/api/ai-agent/farms/${farmId}/recommendations/${runId}/`)
}

export function farmDevicesUrl() {
    return backendUrl("/api/farm-devices/")
}

export function farmLevelsUrl() {
    return backendUrl("/api/farm-levels/")
}

export function farmPowerboardConfigUrl(farmId: number) {
    return backendUrl(`/api/farms/${farmId}/powerboard-config/`)
}

export function deviceStateUrl(deviceId: number) {
    return `${import.meta.env.VITE_BACKEND_BASEURL}/api/devices/${deviceId}/state/`
}

export function aiFarmSettingsUrl(farmId: number) {
    return `${import.meta.env.VITE_BACKEND_BASEURL}/api/ai-agent/farms/${farmId}/settings/`
}

export function aiProviderTestUrl(farmId: number) {
    return `${import.meta.env.VITE_BACKEND_BASEURL}/api/ai-agent/farms/${farmId}/providers/test/`
}

export function aiGenerateUrl(farmId: number) {
    return `${import.meta.env.VITE_BACKEND_BASEURL}/api/ai-agent/farms/${farmId}/recommendations/generate/`
}

export function aiLatestUrl(farmId: number) {
    return `${import.meta.env.VITE_BACKEND_BASEURL}/api/ai-agent/farms/${farmId}/recommendations/latest/`
}

export function aiRecentUrl(farmId: number) {
    return `${import.meta.env.VITE_BACKEND_BASEURL}/api/ai-agent/farms/${farmId}/recommendations/recent/`
}

export function mediaUrl(url: string | null | undefined) {
    if (!url) return null
    if (/^https?:\/\//i.test(url)) return url
    return backendUrl(url.startsWith("/") ? url : `/${url}`)
}

function mediaFileName(url: string) {
    const path = url.split("?")[0].split("#")[0]
    const name = decodeURIComponent(path.split("/").pop() ?? "")
    return name.includes(".") ? name : "image.jpg"
}

export async function downloadMedia(url: string) {
    const response = await fetch(url)
    if (!response.ok) return
    const blob = await response.blob()
    const objectUrl = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = objectUrl
    link.download = mediaFileName(url)
    link.click()
    URL.revokeObjectURL(objectUrl)
}

export function withQuery(url: string, params: Record<string, string | number | boolean | null | undefined>) {
    const search = new URLSearchParams()
    for (const [key, value] of Object.entries(params)) {
        if (value == null || value === "") continue
        search.set(key, String(value))
    }
    const query = search.toString()
    if (!query) return url
    return `${url}${url.includes("?") ? "&" : "?"}${query}`
}

// These IDs must stay aligned with backend/powerboard_control/config.py.
export const POWERBOARD_DEVICE_IDS = {
    phDoser: 1,
    ecDoser: 2,
    pump: 3,
    fan: 4,
    lightLevel1: 5,
    lightLevel2: 6,
}

export const FARM_OVERVIEW_POLL_MS = 30_000
export const AI_AGENT_POLL_MS = 30_000
export const AI_PROVIDERS = ["openrouter", "ollama", "mock"] as const

export const PAGES = {
    noAuthPages: {
        authPage: "/auth"
    },
    authPages: {
        farmOverview: "/farm-overview",
        aiAgent: "/ai-agent",
        growthHarvesting: "/growth-harvesting",
        history: "/history",
        settings: "/settings"
    }
}

export const PAGE_NAMES = {
    noAuthPages: {
        authPage: "Auth Page"
    },
    authPages: {
        farmOverview: "Farm Overview",
        aiAgent: "AI Agent",
        growthHarvesting: "Growth & Harvesting",
        history: "History",
        settings: "Settings"
    }
}

