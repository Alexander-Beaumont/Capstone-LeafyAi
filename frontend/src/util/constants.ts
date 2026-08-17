import type { BABatch, GAGrowingArea } from "./types"


export const SMALL_WINDOW_WIDTH = 1000

export const API = {
    login: `${import.meta.env.VITE_BACKEND_BASEURL}/api/auth/login/`,
    refresh: `${import.meta.env.VITE_BACKEND_BASEURL}/api/auth/refresh/`,
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

export const BaBatches: BABatch[] = [
    {
        plantType: 'Basil',
        batchPlantDate: new Date('2026-06-01'),
        growthStage: 'Vegetative',
        status: 'Active',
        batchId: 'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d',
        growingAreas: [
            { growingAreaName: 'Zone A', slotCount: 48, farmLevel: 1, startDate: new Date('2026-06-01'), endDate: null },
            { growingAreaName: 'Zone B', slotCount: 32, farmLevel: 2, startDate: new Date('2026-06-02'), endDate: new Date('2026-06-20') },
            { growingAreaName: 'Zone C', slotCount: 24, farmLevel: 1, startDate: new Date('2026-06-03'), endDate: new Date('2026-06-22') },
            { growingAreaName: 'Zone D', slotCount: 40, farmLevel: 3, startDate: new Date('2026-06-04'), endDate: new Date('2026-06-25') },
            { growingAreaName: 'Zone E', slotCount: 16, farmLevel: 2, startDate: new Date('2026-06-05'), endDate: new Date('2026-06-27') }
        ]
    },
    {
        plantType: 'Basil',
        batchPlantDate: new Date('2026-05-15'),
        growthStage: 'Harvest Ready',
        status: 'Active',
        batchId: 'f6e5d4c3-b2a1-4c8d-9e0f-1a2b3c4d5e6f',
        growingAreas: [
            { growingAreaName: 'Zone F', slotCount: 20, farmLevel: 1, startDate: new Date('2026-05-15'), endDate: null },
            { growingAreaName: 'Zone G', slotCount: 28, farmLevel: 2, startDate: new Date('2026-05-16'), endDate: new Date('2026-06-10') },
            { growingAreaName: 'Zone H', slotCount: 36, farmLevel: 1, startDate: new Date('2026-05-17'), endDate: new Date('2026-06-11') },
            { growingAreaName: 'Zone I', slotCount: 24, farmLevel: 3, startDate: new Date('2026-05-18'), endDate: new Date('2026-06-12') },
            { growingAreaName: 'Zone J', slotCount: 32, farmLevel: 2, startDate: new Date('2026-05-19'), endDate: new Date('2026-06-14') },
            { growingAreaName: 'Zone K', slotCount: 18, farmLevel: 1, startDate: new Date('2026-05-20'), endDate: new Date('2026-06-15') }
        ]
    },
    {
        plantType: 'Basil',
        batchPlantDate: new Date('2026-04-10'),
        growthStage: 'Harvested',
        status: 'Completed',
        batchId: '9c8b7a6f-5e4d-4b3c-8a2f-1e0d9c8b7a6f',
        growingAreas: [
            { growingAreaName: 'Zone L', slotCount: 40, farmLevel: 1, startDate: new Date('2026-04-10'), endDate: new Date('2026-05-20') },
            { growingAreaName: 'Zone M', slotCount: 40, farmLevel: 3, startDate: new Date('2026-04-12'), endDate: new Date('2026-05-22') },
            { growingAreaName: 'Zone N', slotCount: 22, farmLevel: 2, startDate: new Date('2026-04-13'), endDate: new Date('2026-05-23') },
            { growingAreaName: 'Zone O', slotCount: 30, farmLevel: 1, startDate: new Date('2026-04-14'), endDate: new Date('2026-05-24') },
            { growingAreaName: 'Zone P', slotCount: 26, farmLevel: 2, startDate: new Date('2026-04-15'), endDate: new Date('2026-05-25') }
        ]
    },
    {
        plantType: 'Basil',
        batchPlantDate: new Date('2026-07-01'),
        growthStage: 'Seedling',
        status: 'Active',
        batchId: '3d2c1b0a-9f8e-4d7c-6b5a-4e3d2c1b0a9f',
        growingAreas: [
            { growingAreaName: 'Zone Q', slotCount: 16, farmLevel: 2, startDate: new Date('2026-07-01'), endDate: null },
            { growingAreaName: 'Zone R', slotCount: 20, farmLevel: 1, startDate: new Date('2026-07-02'), endDate: new Date('2026-07-16') },
            { growingAreaName: 'Zone S', slotCount: 24, farmLevel: 3, startDate: new Date('2026-07-03'), endDate: new Date('2026-07-18') },
            { growingAreaName: 'Zone T', slotCount: 18, farmLevel: 1, startDate: new Date('2026-07-04'), endDate: new Date('2026-07-17') },
            { growingAreaName: 'Zone U', slotCount: 34, farmLevel: 2, startDate: new Date('2026-07-05'), endDate: new Date('2026-07-19') }
        ]
    },
    {
        plantType: 'Basil',
        batchPlantDate: new Date('2026-03-01'),
        growthStage: 'Failed',
        status: 'Terminated',
        batchId: '0f1e2d3c-4b5a-4c6d-7e8f-9a0b1c2d3e4f',
        growingAreas: [
            { growingAreaName: 'Zone V', slotCount: 20, farmLevel: 1, startDate: new Date('2026-03-01'), endDate: new Date('2026-03-18') },
            { growingAreaName: 'Zone W', slotCount: 26, farmLevel: 2, startDate: new Date('2026-03-02'), endDate: new Date('2026-03-19') },
            { growingAreaName: 'Zone X', slotCount: 14, farmLevel: 1, startDate: new Date('2026-03-03'), endDate: new Date('2026-03-20') },
            { growingAreaName: 'Zone Y', slotCount: 22, farmLevel: 3, startDate: new Date('2026-03-04'), endDate: new Date('2026-03-21') },
            { growingAreaName: 'Zone Z', slotCount: 30, farmLevel: 2, startDate: new Date('2026-03-05'), endDate: new Date('2026-03-22') }
        ]
    }
]


export const GaGrowingAreas: GAGrowingArea[] = [
    {
        growingAreaName: 'Zone A',
        slotCount: 48,
        farmLevel: 1,
        batches: [
            {
                plantType: 'Basil',
                batchPlantDate: new Date('2026-06-01'),
                growthStage: 'Vegetative',
                status: 'Active',
                batchId: 'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d',
                GrowthAreaStartDate: new Date('2026-06-01'),
                GrowthAreaEndDate: null
            },
            {
                plantType: 'Basil',
                batchPlantDate: new Date('2026-04-10'),
                growthStage: 'Harvested',
                status: 'Completed',
                batchId: '9c8b7a6f-5e4d-4b3c-8a2f-1e0d9c8b7a6f',
                GrowthAreaStartDate: new Date('2026-04-10'),
                GrowthAreaEndDate: new Date('2026-05-20')
            }
        ]
    },
    {
        growingAreaName: 'Zone B',
        slotCount: 32,
        farmLevel: 2,
        batches: [
            {
                plantType: 'Basil',
                batchPlantDate: new Date('2026-05-15'),
                growthStage: 'Harvest Ready',
                status: 'Active',
                batchId: 'f6e5d4c3-b2a1-4c8d-9e0f-1a2b3c4d5e6f',
                GrowthAreaStartDate: new Date('2026-05-15'),
                GrowthAreaEndDate: null
            }
        ]
    },
    {
        growingAreaName: 'Zone C',
        slotCount: 24,
        farmLevel: 1,
        batches: [
            {
                plantType: 'Basil',
                batchPlantDate: new Date('2026-03-01'),
                growthStage: 'Failed',
                status: 'Terminated',
                batchId: '0f1e2d3c-4b5a-4c6d-7e8f-9a0b1c2d3e4f',
                GrowthAreaStartDate: new Date('2026-03-01'),
                GrowthAreaEndDate: new Date('2026-03-18')
            },
            {
                plantType: 'Basil',
                batchPlantDate: new Date('2026-07-01'),
                growthStage: 'Seedling',
                status: 'Active',
                batchId: '3d2c1b0a-9f8e-4d7c-6b5a-4e3d2c1b0a9f',
                GrowthAreaStartDate: new Date('2026-07-01'),
                GrowthAreaEndDate: null
            }
        ]
    },
    {
        growingAreaName: 'Zone D',
        slotCount: 40,
        farmLevel: 3,
        batches: []
    },
    {
        growingAreaName: 'Zone E',
        slotCount: 16,
        farmLevel: 2,
        batches: [
            {
                plantType: 'Basil',
                batchPlantDate: new Date('2026-06-04'),
                growthStage: 'Vegetative',
                status: 'Active',
                batchId: '7b6a5f4e-3d2c-4b1a-9e8f-7d6c5b4a3f2e',
                GrowthAreaStartDate: new Date('2026-06-04'),
                GrowthAreaEndDate: null
            }
        ]
    }
]