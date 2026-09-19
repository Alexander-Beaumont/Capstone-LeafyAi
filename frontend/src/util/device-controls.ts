import { POWERBOARD_DEVICE_IDS } from "./constants"
import type { PowerboardDevice } from "./types"

export const CONTROLLED_DEVICES = [
    { id: POWERBOARD_DEVICE_IDS.phDoser, name: "pH Doser" },
    { id: POWERBOARD_DEVICE_IDS.ecDoser, name: "EC Doser" },
    { id: POWERBOARD_DEVICE_IDS.pump, name: "Irrigation Pump" },
    { id: POWERBOARD_DEVICE_IDS.fan, name: "Farm Fan" },
    { id: POWERBOARD_DEVICE_IDS.lightLevel1, name: "Light Level 1" },
    { id: POWERBOARD_DEVICE_IDS.lightLevel2, name: "Light Level 2" },
]

export function findDevice(devices: PowerboardDevice[], id: number) {
    return devices.find(device => device.device_id === id)
}

export function isControllable(device: PowerboardDevice | undefined) {
    return device?.state === "ON" || device?.state === "OFF"
}

export function isOn(device: PowerboardDevice | undefined) {
    return device?.state === "ON"
}
