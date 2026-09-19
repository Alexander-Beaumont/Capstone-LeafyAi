
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

export interface Farm {
    id: number
    name: string
    location: string
}

export type SensorFreshness = "fresh" | "stale" | "missing"

export interface SensorTrend {
    window_minutes: number
    sample_count: number
    mean: number | null
    minimum: number | null
    maximum: number | null
    change: number | null
    direction: "rising" | "falling" | "stable" | "insufficient_data"
}

export interface FarmSensorState {
    sensor_id: number
    sensor_slug: string
    sensor_type: string
    unit: string
    enabled: boolean
    expected_interval_seconds: number | null
    stale_after_seconds: number
    value: number | null
    as_of: string | null
    measured_at: string | null
    received_at: string | null
    age_seconds: number | null
    status: SensorFreshness
    quality_status: string | null
    quality_notes: string
    source: string | null
    source_channel_id?: string | null
    source_entry_id: number | null
    sensor_reading_id?: number
    trend: SensorTrend
}

export interface FarmDeviceState {
    device_id: number
    device_slug: string
    name: string
    sensors: FarmSensorState[]
    actuator_states: {
        actuator_slug: string
        state: string
        measured_at: string
        received_at: string
        age_seconds: number
        source: string
        source_entry_id: number | null
        quality_status: string
        quality_notes: string
    }[]
    setpoints: {
        setpoint_slug: string
        value: number
        unit: string
        measured_at: string
        received_at: string
        age_seconds: number
        source: string
        source_entry_id: number | null
        quality_status: string
        quality_notes: string
    }[]
    nutrient_tank: {
        capacity_l: number
        current_level_l: number | null
        level_percent: number | null
        as_of: string
        age_seconds: number
        status: SensorFreshness
    } | null
    levels: {
        level_number: number
        cameras: Record<string, unknown>[]
        growing_areas: Record<string, unknown>[]
    }[]
}

export interface FarmState {
    farm_id: number
    generated_at: string
    devices: FarmDeviceState[]
}

export interface PowerboardDevice {
    device_id: number
    name: string
    board: string
    board_ip: string
    child_index: number
    is_on: boolean | null
    state: string
    error?: string
    timestamp: string
}

export interface MagentaState {
    success: boolean
    state: "ON" | "OFF" | "MIXED"
    devices: PowerboardDevice[]
}

export interface DeviceStateResult {
    device_id?: number
    name?: string
    is_on?: boolean | null
    state: string
    success?: boolean
    devices?: PowerboardDevice[]
    detail?: string
}

export interface AISafetyCheck {
    id: number
    decision: number
    checked_at: string
    result: "passed" | "failed"
    explanation: string | null
}

export interface AIDecision {
    id: number
    device: number
    decision_type: string
    category: string
    recommendation: string
    explanation: string
    confidence_score: number | null
    created_at: string
    notification_status: "ready" | "blocked"
    safety_check: AISafetyCheck | null
}