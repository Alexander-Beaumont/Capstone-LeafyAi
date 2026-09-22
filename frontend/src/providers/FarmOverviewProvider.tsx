import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react"
import useLocalStorage from "../components/hooks/useLocalStorage"
import { getDevices, getFarms, getFarmState } from "../util/api-service-layer"
import { FARM_OVERVIEW_POLL_MS } from "../util/constants"
import type { Farm, FarmState, PowerboardDevice } from "../util/types"
import { userContext } from "./UserProvider"

interface FarmOverviewType {
    farmId: number | null
    farmName: string | null
    farmState: FarmState | null
    devices: PowerboardDevice[]
    loading: boolean
    nextRefreshAt: number | null
    setUpdate: (num: number) => void
}

const initialValues: FarmOverviewType = {
    farmId: null,
    farmName: null,
    farmState: null,
    devices: [],
    loading: false,
    nextRefreshAt: null,
    setUpdate: () => null,
}

export const FarmOverviewContext = createContext<FarmOverviewType>(initialValues)

interface Props {
    children: ReactNode
}

export default function FarmOverviewProvider({ children }: Props) {
    const [update, setUpdate] = useState(0)
    const [loading, setLoading] = useState(false)
    const [nextRefreshAt, setNextRefreshAt] = useState<number | null>(null)
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

    useEffect(() => {
        if (!user.loggedIn || !user.accessToken) return

        let cancelled = false
        let timeout: ReturnType<typeof setTimeout> | undefined

        const run = async (notify: boolean) => {
            setLoading(true)
            try {
                const farms = await getFarms(user.accessToken)
                if (!farms.success) {
                    if (notify) alert(farms.msg)
                    return
                }
                const selected = farms.data?.[0]
                if (!selected) {
                    if (notify) alert("No farm found")
                    return
                }
                setFarmJSON(JSON.stringify(selected))

                const state = await getFarmState(user.accessToken, selected.id)
                if (!state.success) {
                    if (notify) alert(state.msg)
                } else {
                    setFarmStateJSON(JSON.stringify(state.data ?? null))
                }

                const board = await getDevices(user.accessToken)
                if (!board.success) {
                    if (notify) alert(board.msg)
                } else {
                    setDevicesJSON(JSON.stringify(board.data ?? []))
                }
            } finally {
                if (cancelled) return
                setLoading(false)
                setNextRefreshAt(Date.now() + FARM_OVERVIEW_POLL_MS)
                timeout = setTimeout(() => run(false), FARM_OVERVIEW_POLL_MS)
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
                farmId: farm?.id ?? null,
                farmName: farm?.name ?? null,
                farmState,
                devices,
                loading,
                nextRefreshAt,
                setUpdate,
            }}
        >
            {children}
        </FarmOverviewContext.Provider>
    )
}
