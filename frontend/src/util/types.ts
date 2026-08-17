
export interface ButtonStyles{
    rightSide?: boolean
    fullWidth?: boolean
    noAnimation?: boolean
}

export interface AuthResult {
    loggedIn: boolean
    accessToken?: string
    msg?: string 
}

export interface SignUpRes{
    user: {
        id: number,
        username: string,
        email: string
    }
    refresh: string
    access: string
}

export interface BABatch{
    plantType: string,
    batchPlantDate: Date,
    growthStage: string,
    status: string,
    batchId: string,
    growingAreas: BAGrowingArea[]
}
export interface BAGrowingArea{
    growingAreaName: string,
    slotCount: number,
    farmLevel: number,
    startDate: Date
    endDate: Date | null
}

export interface GAGrowingArea{
    growingAreaName: string,
    slotCount: number,
    farmLevel: number,
    batches: GABatch[]
}
export interface GABatch{
    plantType: string,
    batchPlantDate: Date,
    growthStage: string,
    status: string,
    batchId: string,
    GrowthAreaStartDate: Date
    GrowthAreaEndDate: Date | null
}