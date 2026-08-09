export const SMALL_WINDOW_WIDTH = 1000

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