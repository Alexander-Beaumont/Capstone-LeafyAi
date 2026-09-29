import { createContext, type ReactNode } from "react"
import type { BABatch, GAGrowingArea } from "../util/types"
import { useState, useEffect, useContext } from "react"
import { userContext } from "./UserProvider"
import useLocalStorage from "../components/hooks/useLocalStorage"
import { useMemo } from "react"
import { getGrowingAreas, getBatches } from "../util/api-service-layer"
import { FarmOverviewContext } from "./FarmOverviewProvider"


interface GrowthHarvestType{
    setUpdate: (num: number) => void
    growingAreas: GAGrowingArea[]
    batches: BABatch[]
}

const initialValues: GrowthHarvestType = {
    setUpdate: () => null,
    growingAreas: [],
    batches: []
}

export const GrowthHarvestingContext = createContext<GrowthHarvestType>(initialValues)

interface Props{
    children: ReactNode
}

export default function GrowthHarvestProvider({children}: Props) {
    const [update, setUpdate] = useState(0)
    const user = useContext(userContext)
    const overview = useContext(FarmOverviewContext)

    const [growingAreasJSON, setGrowingAreasJSON] = useLocalStorage("GA's", "[]")
    const growingAreas = useMemo(() => JSON.parse(growingAreasJSON ?? "[]") as GAGrowingArea[], [growingAreasJSON])

    const [batchesJSON, setBatchesJSON] = useLocalStorage("batches", "[]")
    const batches = useMemo(() => JSON.parse(batchesJSON ?? "[]") as BABatch[], [batchesJSON])

    useEffect(() => {
        const farmId = overview.farmId
        const token = user.accessToken
        let cancelled = false
        const run = async () => {
            if (!token || farmId == null) {
                await Promise.resolve()
                if (cancelled) return
                setGrowingAreasJSON("[]")
                setBatchesJSON("[]")
                return
            }
            const gas = await getGrowingAreas(token, farmId)
            if (cancelled) return
            if(!gas.success){ alert(gas.msg); return; }
            setGrowingAreasJSON(JSON.stringify(gas.data ?? []))

            const bts = await getBatches(token, farmId)
            if (cancelled) return
            if(!bts.success){ alert(bts.msg); return; }
            setBatchesJSON(JSON.stringify(bts.data ?? []))
        }
        if(user.loggedIn) void run()
        return () => { cancelled = true }
    }, [update, user.loggedIn, user.accessToken, overview.farmId, setGrowingAreasJSON, setBatchesJSON])

    return (
        <GrowthHarvestingContext.Provider
            value={{
               batches: batches,
               growingAreas: growingAreas,
               setUpdate: setUpdate
            }}>
            {children}
        </GrowthHarvestingContext.Provider>
    )
}
