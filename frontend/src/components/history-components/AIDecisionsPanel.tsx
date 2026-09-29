import { useContext, useEffect, useState } from "react"
import Panel from "../primatives/Panel"
import IconTitle from "../primatives/IconTitle"
import Dropdown, { type dataFormat } from "../primatives/Dropdown"
import { VscRobot } from "react-icons/vsc"
import { FarmOverviewContext } from "../../providers/FarmOverviewProvider"
import { userContext } from "../../providers/UserProvider"
import { getRecommendationHistory } from "../../util/api-service-layer"
import { Util } from "../../util/Util"
import { localInputToIso } from "../../util/operator"
import type { RecommendationRun } from "../../util/types"
import RunDetails from "../ai-agent/RunDetails"
import Pager from "./Pager"
import DateTimeField from "../primatives/DateTimeField"

const LIMIT = 20

const statuses: dataFormat[] = [
    { id: 0, name: "any status", data: "" },
    { id: 1, name: "pending", data: "pending" },
    { id: 2, name: "running", data: "running" },
    { id: 3, name: "completed", data: "completed" },
    { id: 4, name: "failed", data: "failed" },
    { id: 5, name: "skipped", data: "skipped" },
]

const triggers: dataFormat[] = [
    { id: 0, name: "any trigger", data: "" },
    { id: 1, name: "manual", data: "manual" },
    { id: 2, name: "scheduled", data: "scheduled" },
    { id: 3, name: "legacy", data: "legacy" },
]

const modes: dataFormat[] = [
    { id: 0, name: "any input", data: "" },
    { id: 1, name: "llm", data: "llm" },
    { id: 2, name: "vlm", data: "vlm" },
]

export default function AIDecisionsPanel() {
    const user = useContext(userContext)
    const overview = useContext(FarmOverviewContext)
    const [status, setStatus] = useState(statuses[0])
    const [trigger, setTrigger] = useState(triggers[0])
    const [mode, setMode] = useState(modes[0])
    const [start, setStart] = useState("")
    const [end, setEnd] = useState("")
    const [offset, setOffset] = useState(0)
    const [count, setCount] = useState(0)
    const [runs, setRuns] = useState<RecommendationRun[]>([])
    const [openRunId, setOpenRunId] = useState<number | null>(null)
    const [error, setError] = useState("")
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        if (!user.accessToken || overview.farmId == null) return
        let cancelled = false
        const run = async () => {
            setLoading(true)
            const result = await getRecommendationHistory(user.accessToken, overview.farmId!, {
                status: status.data ? String(status.data) : undefined,
                trigger: trigger.data ? String(trigger.data) : undefined,
                input_mode: mode.data ? String(mode.data) : undefined,
                start: localInputToIso(start),
                end: localInputToIso(end),
                limit: LIMIT,
                offset,
            })
            if (cancelled) return
            setLoading(false)
            if (!result.success || !result.data) {
                setRuns([])
                setCount(0)
                setError(result.msg)
                return
            }
            setError("")
            setRuns(result.data.results)
            setCount(result.data.count)
        }
        run()
        return () => {
            cancelled = true
        }
    }, [user.accessToken, overview.farmId, status, trigger, mode, start, end, offset])

    return (
        <Panel styles="w-full p-3 flex flex-col gap-5">
            <IconTitle title="AI Decisions" icon={<VscRobot size={16}/>} />
            {!overview.farmId ?
                <p className="text-sm text-subtext3">Select a farm to load recommendation history.</p>
            : <>
                <div className="flex flex-wrap gap-3">
                    <Dropdown items={statuses} selectedItem={status} setSelectedItem={id => { setStatus(statuses[id]); setOffset(0) }} showIcon divStyles="w-36" />
                    <Dropdown items={triggers} selectedItem={trigger} setSelectedItem={id => { setTrigger(triggers[id]); setOffset(0) }} showIcon divStyles="w-36" />
                    <Dropdown items={modes} selectedItem={mode} setSelectedItem={id => { setMode(modes[id]); setOffset(0) }} showIcon divStyles="w-32" />
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                    <DateTimeField name="Start" value={start} setValue={value => { setStart(value); setOffset(0) }} />
                    <DateTimeField name="End" value={end} setValue={value => { setEnd(value); setOffset(0) }} />
                </div>
                {error ? <p className="text-xs text-high">{error}</p> : null}
                {loading && runs.length === 0 ?
                    <div className="h-24 bg-panel2 animate-pulse rounded-md" />
                : runs.length === 0 ?
                    <p className="text-sm text-subtext3">No recommendation runs yet.</p>
                :
                    <div className="flex flex-col gap-3">
                        {runs.map(run => {
                            const open = openRunId === run.id
                            return (
                                <div key={run.id} className="border border-border rounded-lg bg-panel2 p-3 flex flex-col gap-3">
                                    <button
                                        type="button"
                                        className="flex flex-wrap items-center justify-between gap-2 text-left hover:cursor-pointer"
                                        onClick={() => setOpenRunId(open ? null : run.id)}
                                        aria-expanded={open}
                                    >
                                        <span className="text-sm text-title font-semibold">Run {run.id}</span>
                                        <span className="text-xs text-subtext3">
                                            {Util.formatDateTime(new Date(run.completed_at ?? run.created_at))}
                                            {" · "}
                                            {open ? "Hide" : "Details"}
                                        </span>
                                    </button>
                                    {open ? <RunDetails run={run} /> : <RunDetails run={run} compact />}
                                </div>
                            )
                        })}
                    </div>
                }
                <Pager offset={offset} limit={LIMIT} count={count} onOffset={setOffset} />
            </>}
        </Panel>
    )
}
