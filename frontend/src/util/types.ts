
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

interface APISuccess<T> {
  success: true;
  msg: string;
  data: T;
}

interface APIFailure {
  success: false;
  msg: string;
}

export type APIResult<T> = APISuccess<T> | APIFailure;

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
    GrowthAreaStartDate: Date
    GrowthAreaEndDate: Date | null
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