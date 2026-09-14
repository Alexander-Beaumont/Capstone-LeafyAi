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


export const BACKEND_BASEURL = (import.meta.env.VITE_BACKEND_BASEURL || "http://127.0.0.1:8000").replace(/\/$/, "")
export const POWERBOARD_BASEURL = (import.meta.env.VITE_POWERBOARD_BASEURL || "http://127.0.0.1:8010").replace(/\/$/, "")

export const API_ROUTES = {
    login: `${BACKEND_BASEURL}/api/auth/login/`,
    signup: `${BACKEND_BASEURL}/api/auth/register/`,
    refresh: `${BACKEND_BASEURL}/api/auth/refresh/`,
    getGrowingAreas: `${BACKEND_BASEURL}/api/growing-areas/`,
    getBatches: `${BACKEND_BASEURL}/api/batches/`,
    moveBatch: `${BACKEND_BASEURL}/api/move-batch/`,
    createGrowingArea: `${BACKEND_BASEURL}/api/create-growing-area/`,
    updateGrowingAreas: `${BACKEND_BASEURL}/api/update-growing-area/`,
    updateBatch: `${BACKEND_BASEURL}/api/update-batch/`,
    createBatch: `${BACKEND_BASEURL}/api/create-batch/`,
    deleteGrowingArea: `${BACKEND_BASEURL}/api/delete-growing-area/`,
    cameras: `${BACKEND_BASEURL}/api/cameras/`,
    farmLevels: `${BACKEND_BASEURL}/api/farm-levels/`,
    sensors: `${BACKEND_BASEURL}/api/sensors/`,
    sensorReadings: `${BACKEND_BASEURL}/api/sensor-readings/`,
    powerDevices: `${POWERBOARD_BASEURL}/api/devices/`,
}

export const PAGES = {
    noAuthPages: {
        landingPage: "/",
        authPage: "/auth"
    },
    authPages: {
        farmOverview: "/farm-overview",
        plantVision: "/plant-vision",
        aiAgent: "/ai-agent",
        growthHarvesting: "/growth-harvesting",
        history: "/history",
        settings: "/settings"
    }
}

export const PAGE_NAMES = {
    noAuthPages: {
        landingPage: "Landing Page",
        authPage: "Auth Page"
    },
    authPages: {
        farmOverview: "Farm Overview",
        plantVision: "Plant Vision",
        aiAgent: "AI Agent",
        growthHarvesting: "Growth & Harvesting",
        history: "History",
        settings: "Settings"
    }
}

export  const placeHolderDecisions = [{   
    name: "Run Pump",
    change: "AI agent has requested to run the pump at 2L/min for 45 seconds",
    reason: "Water level has decreased to 20%, ideal range is above 50%",
    decisionSeverity: "High",
    approved: false,
    approver: "James"
},{
    name: "Dim Lights",
    change: "AI agent has requested to dim the lights from 60% to 55%",
    reason: " To simulate natural cycles it is recommended to dim the ligths to 55%",
    decisionSeverity: "Low",
    approved: false,
    approver: "Aiden"
},{
    name: "Run Doser",
    change: "AI agent has requested to run the doser for 10 seconds",
    reason: " pH level has been trending down",
    decisionSeverity: "Medium",
    approved: true,
    approver: "Leam"
}]



