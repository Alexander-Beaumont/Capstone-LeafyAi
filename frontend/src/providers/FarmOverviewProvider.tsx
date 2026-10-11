import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react"
import useLocalStorage from "../components/hooks/useLocalStorage"
import { getDevices, getFarmDashboard, getFarms, getFarmState, getSensorIngest } from "../util/api-service-layer"
import { FARM_OVERVIEW_POLL_MS } from "../util/constants"
import type { Farm, FarmDashboard, FarmState, PowerboardDevice } from "../util/types"
import { userContext } from "./UserProvider"

interface FarmOverviewType {
    farms: Farm[]
    farmId: number | null
    farmName: string | null
    farmState: FarmState | null
    devices: PowerboardDevice[]
    dashboard: FarmDashboard | null
    loading: boolean
    farmsLoaded: boolean
    loadError: string
    nextRefreshAt: number | null
    setUpdate: (num: number) => void
    selectFarm: (farm: Farm) => void
}

const initialValues: FarmOverviewType = {
    farms: [],
    farmId: null,
    farmName: null,
    farmState: null,
    devices: [],
    dashboard: null,
    loading: false,
    farmsLoaded: false,
    loadError: "",
    nextRefreshAt: null,
    setUpdate: () => null,
    selectFarm: () => null,
}

export const FarmOverviewContext = createContext<FarmOverviewType>(initialValues)

interface Props {
    children: ReactNode
}

export default function FarmOverviewProvider({ children }: Props) {
    const [update, setUpdate] = useState(0)
    const [loading, setLoading] = useState(false)
    const [farmsLoaded, setFarmsLoaded] = useState(false)
    const [loadError, setLoadError] = useState("")
    const [nextRefreshAt, setNextRefreshAt] = useState<number | null>(null)
    const [farms, setFarms] = useState<Farm[]>([])
    const [dashboard, setDashboard] = useState<FarmDashboard | null>(null)
    const user = useContext(userContext)

    // Keep the selected farm and latest overview data across page navigation;
    // server data is still refreshed on the polling cycle below.
    const [farmJSON, setFarmJSON] = useLocalStorage("selectedFarm", "null")
    const farm = useMemo(
        () => JSON.parse(farmJSON ?? "null") as Farm | null,
        [farmJSON],
    )

    const [farmStateJSON, setFarmStateJSON] = useLocalStorage("farmState", "null")
    const farmState = useMemo(
        () => JSON.parse(farmStateJSON ?? "null") as FarmState | null,
        [farmStateJSON],
    )

    const [devicesJSON, setDevicesJSON] = useLocalStorage("powerboardDevices", "[]")
    const devices = useMemo(
        () => JSON.parse(devicesJSON ?? "[]") as PowerboardDevice[],
        [devicesJSON],
    )

    function selectFarm(next: Farm) {
        setDashboard(null)
        setFarmJSON(JSON.stringify(next))
        setUpdate(value => value + 1)
    }

    useEffect(() => {
        if (!user.loggedIn || !user.accessToken) return

        let cancelled = false
        let timeout: ReturnType<typeof setTimeout> | undefined

        const run = async () => {
            setLoading(true)
            let refreshMs = FARM_OVERVIEW_POLL_MS
            try {
                const farmsResult = await getFarms(user.accessToken)
                if (!farmsResult.success || !farmsResult.data) {
                    if (!cancelled) setLoadError(farmsResult.msg || "Could not load farms")
                    return
                }
                const list = farmsResult.data.results ?? []
                if (!cancelled) {
                    setFarms(list)
                    setLoadError("")
                }

                const selected = farm ? list.find(item => item.id === farm.id) ?? null : null
                if (!selected) {
                    if (farm) setFarmJSON("null")
                    setFarmStateJSON("null")
                    setDashboard(null)
                    const board = await getDevices(user.accessToken)
                    if (!cancelled && board.success) setDevicesJSON(JSON.stringify(board.data ?? []))
                    return
                }
                if (!farm || selected.id !== farm.id || selected.name !== farm.name || selected.location !== farm.location) {
                    setFarmJSON(JSON.stringify(selected))
                }

                // Load the four independent overview sources in parallel so one
                // slow hardware-facing API does not serialize the whole refresh.
                const [state, board, dash, ingest] = await Promise.all([
                    getFarmState(user.accessToken, selected.id),
                    getDevices(user.accessToken, selected.id),
                    getFarmDashboard(user.accessToken, selected.id),
                    getSensorIngest(user.accessToken, selected.id),
                ])
                if (cancelled) return
                const problems: string[] = []
                if (!state.success) {
                    problems.push(state.msg)
                } else {
                    setFarmStateJSON(JSON.stringify(state.data ?? null))
                }
                if (!board.success) {
                    problems.push(board.msg)
                } else {
                    setDevicesJSON(JSON.stringify(board.data ?? []))
                }
                if (!dash.success) {
                    problems.push(dash.msg)
                } else {
                    setDashboard(dash.data ?? null)
                }
                setLoadError(problems.filter(Boolean).join(" "))
                if (ingest.success && ingest.data) {
                    const intervals = ingest.data.results
                        .map(config => config.poll_interval_seconds)
                        .filter(seconds => Number.isInteger(seconds) && seconds >= 1 && seconds <= 86400)
                    if (intervals.length) refreshMs = Math.min(...intervals) * 1000
                }
            } finally {
                if (!cancelled) {
                    setLoading(false)
                    setFarmsLoaded(true)
                    setNextRefreshAt(Date.now() + refreshMs)
                    timeout = setTimeout(() => run(), refreshMs)
                }
            }
        }

        run()
        return () => {
            cancelled = true
            if (timeout) clearTimeout(timeout)
        }
    }, [update, user.loggedIn, user.accessToken])

    return (
        <FarmOverviewContext.Provider
            value={{
                farms,
                farmId: farm?.id ?? null,
                farmName: farm?.name ?? null,
                farmState,
                devices,
                dashboard,
                loading,
                farmsLoaded,
                loadError,
                nextRefreshAt,
                setUpdate,
                selectFarm,
            }}
        >
            {children}
        </FarmOverviewContext.Provider>
    )
}
