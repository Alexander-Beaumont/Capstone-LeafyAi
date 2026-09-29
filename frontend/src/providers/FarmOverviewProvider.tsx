import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react"
import useLocalStorage from "../components/hooks/useLocalStorage"
import { getDevices, getFarmDashboard, getFarms, getFarmState } from "../util/api-service-layer"
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
    const [nextRefreshAt, setNextRefreshAt] = useState<number | null>(null)
    const [farms, setFarms] = useState<Farm[]>([])
    const [dashboard, setDashboard] = useState<FarmDashboard | null>(null)
    const user = useContext(userContext)

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

        const run = async (notify: boolean) => {
            setLoading(true)
            try {
                const farmsResult = await getFarms(user.accessToken)
                if (!farmsResult.success || !farmsResult.data) {
                    if (notify) alert(farmsResult.msg)
                    return
                }
                const list = farmsResult.data.results ?? []
                if (!cancelled) setFarms(list)

                const selected = farm ? list.find(item => item.id === farm.id) ?? null : null
                if (!selected) {
                    if (farm) setFarmJSON("null")
                    setFarmStateJSON("null")
                    setDashboard(null)
                    const board = await getDevices(user.accessToken)
                    if (!cancelled && board.success) setDevicesJSON(JSON.stringify(board.data ?? []))
                    if (list.length === 0 && notify) alert("No farm found")
                    return
                }
                if (!farm || selected.id !== farm.id || selected.name !== farm.name || selected.location !== farm.location) {
                    setFarmJSON(JSON.stringify(selected))
                }

                const [state, board, dash] = await Promise.all([
                    getFarmState(user.accessToken, selected.id),
                    getDevices(user.accessToken),
                    getFarmDashboard(user.accessToken, selected.id),
                ])
                if (cancelled) return
                if (!state.success) {
                    if (notify) alert(state.msg)
                } else {
                    setFarmStateJSON(JSON.stringify(state.data ?? null))
                }
                if (!board.success) {
                    if (notify) alert(board.msg)
                } else {
                    setDevicesJSON(JSON.stringify(board.data ?? []))
                }
                if (!dash.success) {
                    if (notify) alert(dash.msg)
                    setDashboard(null)
                } else {
                    setDashboard(dash.data ?? null)
                }
            } finally {
                if (!cancelled) {
                    setLoading(false)
                    setNextRefreshAt(Date.now() + FARM_OVERVIEW_POLL_MS)
                    timeout = setTimeout(() => run(false), FARM_OVERVIEW_POLL_MS)
                }
            }
        }

        run(true)
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
                nextRefreshAt,
                setUpdate,
                selectFarm,
            }}
        >
            {children}
        </FarmOverviewContext.Provider>
    )
}
