import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react"
import useLocalStorage from "../components/hooks/useLocalStorage"
import { getAiDecisions, getDevices, getFarms, getFarmState } from "../util/api-service-layer"
import { FARM_OVERVIEW_POLL_MS } from "../util/constants"
import type { AIDecision, FarmState, PowerboardDevice } from "../util/types"
import { userContext } from "./UserProvider"

interface FarmOverviewType {
    farmState: FarmState | null
    devices: PowerboardDevice[]
    decisions: AIDecision[]
    loading: boolean
    nextRefreshAt: number | null
    setUpdate: (num: number) => void
}

const initialValues: FarmOverviewType = {
    farmState: null,
    devices: [],
    decisions: [],
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

    const [decisionsJSON, setDecisionsJSON] = useLocalStorage("aiDecisions", "[]")
    const decisions = useMemo(
        () => JSON.parse(decisionsJSON ?? "[]") as AIDecision[],
        [decisionsJSON],
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
                const farm = farms.data?.[0]
                if (!farm) {
                    if (notify) alert("No farm found")
                    return
                }

                const state = await getFarmState(user.accessToken, farm.id)
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

                const ai = await getAiDecisions(user.accessToken)
                if (!ai.success) {
                    if (notify) alert(ai.msg)
                } else {
                    setDecisionsJSON(JSON.stringify(ai.data ?? []))
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
                farmState,
                devices,
                decisions,
                loading,
                nextRefreshAt,
                setUpdate,
            }}
        >
            {children}
        </FarmOverviewContext.Provider>
    )
}
