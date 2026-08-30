import { createContext, type ReactNode } from "react"
import type { BABatch, GAGrowingArea } from "../util/types"
import { useState, useEffect, useContext } from "react"
import { userContext } from "./UserProvider"
import useLocalStorage from "../components/hooks/useLocalStorage"
import { useMemo } from "react"
import { getGrowingAreas, getBatches } from "../util/api-service-layer"


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

    const [growingAreasJSON, setGrowingAreasJSON] = useLocalStorage("GA's", "[]")
    const growingAreas = useMemo(() => JSON.parse(growingAreasJSON ?? "[]") as GAGrowingArea[], [growingAreasJSON])

    const [batchesJSON, setBatchesJSON] = useLocalStorage("batches", "[]")
    const batches = useMemo(() => JSON.parse(batchesJSON ?? "[]") as BABatch[], [batchesJSON])

    useEffect(() => {
        const run = async () => {
            const gas = await getGrowingAreas(user.accessToken)
            if(!gas.success){ alert(gas.msg); return; }
            setGrowingAreasJSON(JSON.stringify(gas.data))

            const bts = await getBatches(user.accessToken)
            if(!bts.success){ alert(bts.msg); return; }
            setBatchesJSON(JSON.stringify(bts.data))
        }
        if(user.loggedIn) run()
    }, [update])

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
