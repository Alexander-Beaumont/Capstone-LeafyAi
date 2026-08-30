
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

export type APIResult<T> = {
    success: boolean;
    msg: string;
    data?: T;
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
    batchPlantDate: string,
    growthStage: string,
    status: string,
    batchId: string,
    growingAreas: BAGrowingArea[]
}
export interface BAGrowingArea{
    growingAreaName: string,
    slotCount: number,
    farmLevel: number,
    startDate: string
    endDate: string | null
}

export interface GAGrowingArea{
    growingAreaId: string,
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
    GrowthAreaStartDate: string
    GrowthAreaEndDate: string | null
}

export interface MoveBatch{
    currentGaID: string,
    destinationGaID: string,
    batchID: string
}

export interface GaDefinition{
    growingAreaID?: string
    name: string,
	farmLevel: number,
	slotCount: number
}

export interface BatchDefinition {
    plantType: string;
    growthStage: string;
    status: string;
    growingAreaID: string;
}