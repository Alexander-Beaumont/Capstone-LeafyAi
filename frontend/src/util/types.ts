
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

export interface Page<T> {
    count: number
    next: string | null
    previous: string | null
    results: T[]
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
    location: string | null
}

export interface CameraImage {
    id: number
    camera: number
    captured_at: string
    path: string | null
    vlm_ready: boolean
    quality_status: string
    quality_flags: string[]
    quality_message: string
    quality_metrics: Record<string, unknown>
}

export interface DashboardImageQuality {
    status: string
    flags: string[]
    message: string
    vlm_ready: boolean
}

export interface FarmDashboard {
    farm: Farm
    generated_at: string
    sensors: {
        counts: {
            total: number
            fresh: number
            stale: number
            missing: number
            suspect: number
        }
        ingestion_status: "not_configured" | "disabled" | "healthy" | "error"
        last_successful_collection: string | null
        devices: number
    }
    cameras: {
        count: number
        latest_image: CameraImage | null
        image_quality: DashboardImageQuality | null
        next_capture: string | null
    }
    ai: {
        schedule_state: "enabled" | "disabled"
        next_eligible_window: string | null
        latest_run: RecommendationRun | null
        action_summary: {
            recommendations: number
            automatic: number
            hardware_actions: number
        }
    }
}

export interface SensorIngestConfiguration {
    id: number
    farm_id: number
    device_id: number
    device_name: string
    device_slug: string
    enabled: boolean
    water_quality_url: string
    ambient_sensor_url: string
    poll_interval_seconds: number
    sensor_stale_threshold_seconds: number
    last_attempt_at: string | null
    last_success_at: string | null
    last_error: string
    consecutive_failures: number
    updated_at: string
}

export interface SensorIngestPatch {
    enabled?: boolean
    water_quality_url?: string
    ambient_sensor_url?: string
    poll_interval_seconds?: number
    sensor_stale_threshold_seconds?: number
}

export interface SensorCollectionResult {
    stored_count: number
    missing_sensors: string[]
    invalid_sensors: string[]
    collected_at: string
    validated: boolean
    ingest_status: SensorIngestConfiguration
}

export interface SensorReadingRecord {
    id: number
    sensor: number
    sensor_slug: string
    sensor_type: string
    unit: string
    value: string
    measured_at: string
    received_at: string
    source: string
    source_channel_id: string
    source_entry_id: number | null
    quality_status: string
    quality_notes: string
}

export interface SensorHistoryPoint {
    timestamp: string
    minimum: number
    maximum: number
    average: number
    latest: number
    sample_count: number
}

export interface SensorHistorySeries {
    sensor_id: number
    sensor_slug: string
    sensor_type: string
    unit: string
    points: SensorHistoryPoint[]
}

export interface SensorHistory {
    preset: string
    start: string
    end: string
    bucket_seconds: number
    series: SensorHistorySeries[]
}

export type CameraScheduleState = "due" | "scheduled" | "outside_window" | "disabled" | "archived"

export interface CameraImageQuality {
    status: string
    flags: string[]
    message: string
    metrics: Record<string, unknown>
    vlm_ready: boolean
}

export interface FarmCamera {
    id: number
    farm_level_id: number
    name: string
    position: string | null
    source_type: string
    ip_address: string | null
    rtsp_port: number | null
    rtsp_path: string | null
    enabled: boolean
    is_archived: boolean
    capture_interval_minutes: number
    active_start_time: string | null
    active_end_time: string | null
    latest_image: CameraImage | null
    last_capture_at: string | null
    next_scheduled_capture: string | null
    schedule_state: CameraScheduleState
    image_quality: CameraImageQuality | null
}

export interface CameraWrite {
    farm_level_id: number
    name: string
    position?: string
    source_type: "RTSP"
    ip_address: string
    rtsp_port: number
    rtsp_path: string
    enabled: boolean
    capture_interval_minutes: number
    active_start_time: string | null
    active_end_time: string | null
}

export interface GalleryImage extends CameraImage {
    camera_name: string
    ai_used: boolean
    ai_run_ids: number[]
}

export interface FarmLevel {
    id: number
    device: number
    level_number: number
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

export type AIProviderName = "openrouter" | "ollama" | "mock"
export type RecommendationTrigger = "manual" | "scheduled" | "legacy"
export type RecommendationStatus = "pending" | "running" | "completed" | "failed" | "skipped"
export type RecommendationInputMode = "vlm" | "llm"
export type RecommendationExecutionType = "notification" | "automated"
export type RecommendationTargetDevice =
    | "fans"
    | "light"
    | "irrigation_pump"
    | "nutrient_doser"
    | "ph_doser"
    | "none"
export type RecommendationDeviceState = "on" | "off" | "none"
export type RecommendationCategory = "climate" | "lighting" | "dosing" | "water" | "harvest" | "alert"
export type QualityStatus = "PASS" | "WARN" | "FAIL" | "UNKNOWN" | string
export type FarmActionResult = "success" | "failed" | "partial"

export interface AIConfiguration {
    farm: number
    llm_provider: AIProviderName
    llm_model: string
    llm_api_key_configured: boolean
    llm_api_key_mask: string
    vlm_provider: AIProviderName
    vlm_model: string
    vlm_api_key_configured: boolean
    vlm_api_key_mask: string
    schedule_enabled: boolean
    timezone: string
    interval_minutes: number
    active_start_time: string
    active_end_time: string
    max_images: number
    max_image_age_minutes: number
    updated_at: string
}

export interface AIConfigurationPatch {
    llm_provider?: AIProviderName
    llm_model?: string
    llm_api_key?: string
    vlm_provider?: AIProviderName
    vlm_model?: string
    vlm_api_key?: string
    clear_llm_api_key?: boolean
    clear_vlm_api_key?: boolean
    schedule_enabled?: boolean
    timezone?: string
    interval_minutes?: number
    active_start_time?: string
    active_end_time?: string
    max_images?: number
    max_image_age_minutes?: number
}

export interface SourceImage {
    id: number
    camera_id: number
    camera_name: string
    captured_at: string
    age_seconds: number
    reused: boolean
    url: string | null
    quality_status: QualityStatus
    quality_flags: string[]
    quality_message: string
    vlm_ready: boolean
}

export interface SourceReading {
    id: number
    sensor_id: number
    sensor_slug: string
    sensor_type: string
    value: number
    unit: string
    measured_at: string
    age_seconds: number
    quality_status: string
    reused: boolean
}

export interface InputFreshnessSummary {
    evaluated_at?: string
    max_image_age_minutes: number
    sensors: {
        fresh: number
        stale: number
        missing: number
        suspect: number
        included: number
    }
    images: {
        latest_candidates: number
        technically_eligible: number
        included: number
    }
    previous_completed_run_id?: number | null
    new_reading_ids: number[]
    reused_reading_ids: number[]
    new_image_ids: number[]
    reused_image_ids: number[]
}

export interface VisualEvidence {
    image_id: number
    camera_id: number
    camera_name: string
    captured_at: string
    quality_status: QualityStatus
    quality_flags: string[]
    quality_message: string
    vlm_ready: boolean
    selected: boolean
    reason: string
}

export interface ImageObservation {
    camera_id?: number
    observation?: string
    [key: string]: unknown
}

export interface AISafetyCheck {
    id: number
    decision: number
    checked_at: string
    result: "passed" | "failed"
    explanation: string | null
}

export interface FarmAction {
    id: number
    decision: number
    target_device: string
    powerboard_device_ids: number[]
    requested_state: string
    previous_state: string
    confirmed_state: string
    attempted_at: string | null
    executed_at: string | null
    result: FarmActionResult | null
    explanation: string | null
    hardware_response: Record<string, unknown>
}

export interface AIDecision {
    id: number
    run?: number
    device: number
    decision_type: string
    execution_type?: RecommendationExecutionType
    target_device?: RecommendationTargetDevice
    device_state?: RecommendationDeviceState
    category: string
    recommendation: string
    explanation: string
    confidence_score: string | number | null
    output_used_fallback?: boolean
    created_at: string
    notification_status: "ready" | "blocked"
    safety_check: AISafetyCheck | null
    actions?: FarmAction[]
}

export interface RecommendationRun {
    id: number
    farm: number
    trigger: RecommendationTrigger
    status: RecommendationStatus
    scheduled_for: string | null
    input_mode: RecommendationInputMode
    provider_name: string
    model_name: string
    source_images: SourceImage[]
    source_readings: SourceReading[]
    input_freshness_summary: InputFreshnessSummary
    skip_reason: string
    visual_evidence: VisualEvidence[]
    image_observations: ImageObservation[]
    fallback_used: boolean
    fallback_reason: string
    error: string
    created_at: string
    started_at: string | null
    completed_at: string | null
    recommendations: AIDecision[]
}

export interface ProviderTestResult {
    success: boolean
    provider?: string
    model?: string
    response?: string
    detail?: string
    failures?: string[]
}

export type ProviderTestRole = "llm" | "vlm"