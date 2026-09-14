export interface ButtonStyles {
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
    success: boolean
    msg: string
    data?: T
    status?: number
}

export interface SignUpRes {
    user: { id: number; username: string; email: string }
    refresh: string
    access: string
}

export interface BABatch {
    plantType: string
    batchPlantDate: string
    growthStage: string
    status: string
    batchId: string
    growingAreas: BAGrowingArea[]
}
export interface BAGrowingArea {
    growingAreaName: string
    slotCount: number
    farmLevel: number
    startDate: string
    endDate: string | null
}
export interface GAGrowingArea {
    growingAreaId: string
    growingAreaName: string
    slotCount: number
    farmLevel: number
    batches: GABatch[]
}
export interface GABatch {
    plantType: string
    batchPlantDate: Date
    growthStage: string
    status: string
    batchId: string
    GrowthAreaStartDate: string
    GrowthAreaEndDate: string | null
}
export interface MoveBatch {
    currentGaID: string
    destinationGaID: string
    batchID: string
}
export interface GaDefinition {
    growingAreaID?: string
    name: string
    farmLevel: number
    slotCount: number
}
export interface BatchDefinition {
    plantType: string
    growthStage: string
    status: string
    growingAreaID: string
}

export interface FarmLevel {
    id: number
    device: number
    level_number: number
}

export interface RoiRect {
    x: number
    y: number
    width: number
    height: number
}

export interface Camera {
    id: number
    farm_level_id: number
    name: string
    position: string | null
    source_type: "RTSP"
    ip_address: string | null
    rtsp_port: number | null
    rtsp_path: string | null
    enabled: boolean
    cv_enabled: boolean
    is_archived: boolean
    capture_interval_minutes: number
    active_start_time: string | null
    active_end_time: string | null
    roi_points: RoiRect | null
    growth_baseline_reset_at: string | null
}

export type CameraInput = Omit<Camera, "id" | "growth_baseline_reset_at" | "is_archived"> & {
    growth_baseline_reset_at?: string | null
    is_archived?: boolean
}

export interface LatestImage {
    image_id: number
    camera_id: number
    captured_at: string
    image_url: string
}

export interface CvAnalysis {
    id: number
    image: number
    created_at: string
    total_canopy_coverage: string | null
    growth_change: string | null
    crowding_percentage: string | null
    green_percentage: string | null
    yellow_percentage: string | null
    measurement_valid: boolean
    processing_time_ms: number | null
    vlm_ready: boolean
    quality_status: "PASS" | "FAIL" | "UNKNOWN"
    quality_flags: string[]
    quality_message: string
}

export interface LatestAnalysis {
    camera_id: number
    image_id: number
    captured_at: string
    image_url: string
    analysis: CvAnalysis
}

export interface Sensor {
    id: number
    device: number
    sensor_type: string
    unit: string
}

export interface SensorReading {
    id: number
    sensor: number
    timestamp: string
    value: string
}

export interface PowerDevice {
    device_id: number
    name: string
    is_on: boolean | null
    state: "ON" | "OFF" | "ERROR"
    timestamp: string
    error?: string
}
