import { useContext, useMemo, useState } from "react"
import { Link } from "react-router"
import { VscRobot } from "react-icons/vsc"
import { GoGear } from "react-icons/go"
import PageTitlePanel from "../components/primatives/PageTitlePanel"
import Panel from "../components/primatives/Panel"
import IconTitle from "../components/primatives/IconTitle"
import Button from "../components/primatives/Button"
import { FarmOverviewContext } from "../providers/FarmOverviewProvider"
import { AiAgentContext } from "../providers/AiAgentProvider"
import { PAGES, POWERBOARD_DEVICE_IDS } from "../util/constants"
import { actionSummary, formatInTimeZone, inputModeLabel, nextScheduleTime } from "../util/ai-agent"
import RunDetails from "../components/ai-agent/RunDetails"
import Badge from "../components/ai-agent/Badge"
import StatusCard from "../components/ai-agent/StatusCard"

export default function AiAgent() {
    const overview = useContext(FarmOverviewContext)
    const ai = useContext(AiAgentContext)
    const [openRunId, setOpenRunId] = useState<number | null>(null)

    const nextSchedule = useMemo(
        () => nextScheduleTime(ai.settings),
        [ai.settings, ai.latestRun],
    )

    const farmLabel = overview.farmName ?? "Farm"
    const scheduleLabel = ai.settings?.schedule_enabled ? "Schedule on" : "Schedule off"
    const providerStatus = ai.settings
        ? `${ai.settings.llm_provider} / ${ai.settings.vlm_provider}`
        : "Loading"
    const lastMode = inputModeLabel(ai.latestRun?.input_mode, ai.latestRun?.fallback_used)
    const nextLabel = !ai.settings
        ? "…"
        : !ai.settings.schedule_enabled
            ? "Off"
            : nextSchedule
                ? formatInTimeZone(nextSchedule, ai.settings.timezone)
                : "Outside window"

    return (
        <div className="flex flex-col w-full items-center p-5 max-w-250 m-auto gap-5">
            <PageTitlePanel
                title="AI Agent"
                icon={<VscRobot/>}
                refresh
                refreshing={ai.loading}
                refreshLabel={ai.loading ? "Refreshing…" : farmLabel}
                onRefresh={() => ai.refresh()}
                actions={
                    <Link
                        to={PAGES.authPages.settings}
                        aria-label="Settings"
                        className="text-subtext2 hover:text-highlight"
                    >
                        <GoGear size={18} />
                    </Link>
                }
            />

            <Panel styles="w-full p-3 px-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex flex-col gap-2">
                    <p className="text-title text-lg font-semibold">{farmLabel}</p>
                    <div className="flex flex-wrap gap-2">
                        <Badge label={scheduleLabel} tone={ai.settings?.schedule_enabled ? "ok" : "default"} />
                        {ai.generating ? <Badge label="Generating" tone="warn" /> : null}
                    </div>
                </div>
                <Button
                    name="Generate now"
                    highlight
                    loading={ai.generating}
                    onSubmit={async () => { await ai.generateNow() }}
                />
            </Panel>
            {ai.generateError ? <p className="w-full text-sm text-high">{ai.generateError}</p> : null}
            {ai.runsError ? <p className="w-full text-sm text-high">{ai.runsError}</p> : null}

            <div className="grid grid-cols-1 sm:grid-cols-2 w-full gap-3">
                <StatusCard
                    name="Providers"
                    value={providerStatus}
                    hint={ai.settings ? `LLM ${ai.settings.llm_model}` : undefined}
                    loading={ai.loading && !ai.settings}
                />
                <StatusCard
                    name="Next schedule"
                    value={nextLabel}
                    hint={ai.settings?.timezone}
                    loading={ai.loading && !ai.settings}
                />
                <StatusCard
                    name="Last input"
                    value={ai.latestRun ? lastMode : "None"}
                    hint={ai.latestRun?.fallback_used ? "Fell back to sensors" : ai.latestRun?.model_name}
                    loading={ai.loading && !ai.latestRun}
                />
                <StatusCard
                    name="Actions"
                    value={ai.latestRun ? String((ai.latestRun.recommendations ?? []).flatMap(item => item.actions ?? []).length) : "0"}
                    hint={actionSummary(ai.latestRun)}
                    loading={ai.loading && !ai.latestRun}
                />
            </div>

            <Panel styles="w-full p-3 px-4 flex flex-col gap-4">
                <IconTitle title="Latest run" icon={<VscRobot size={16}/>} />
                {ai.loading && !ai.latestRun ?
                    <div className="h-32 bg-panel2 animate-pulse rounded-md" />
                : !ai.latestRun ?
                    <p className="text-sm text-subtext3">No recommendation run exists for this farm yet.</p>
                :
                    <RunDetails run={ai.latestRun} />
                }
            </Panel>

            <Panel styles="w-full p-3 px-4 flex flex-col gap-4">
                <IconTitle title="Recent runs" icon={<VscRobot size={16}/>} />
                {ai.loading && ai.recentRuns.length === 0 ?
                    <div className="h-24 bg-panel2 animate-pulse rounded-md" />
                : ai.recentRuns.length === 0 ?
                    <p className="text-sm text-subtext3">No recent runs.</p>
                :
                    <div className="flex flex-col gap-3">
                        {ai.recentRuns.map(run => {
                            const open = openRunId === run.id
                            return (
                                <div key={run.id} className="border border-border rounded-lg bg-panel2 p-3 flex flex-col gap-3">
                                    <button
                                        type="button"
                                        className="flex flex-wrap items-center justify-between gap-2 text-left hover:cursor-pointer"
                                        onClick={() => setOpenRunId(open ? null : run.id)}
                                        aria-expanded={open}
                                    >
                                        <span className="text-sm text-subtext1 font-semibold">
                                            Run {run.id} · {run.status} · {inputModeLabel(run.input_mode, run.fallback_used)}
                                        </span>
                                        <span className="text-xs text-subtext3">{open ? "Hide" : "Details"}</span>
                                    </button>
                                    {open ? <RunDetails run={run} /> : <RunDetails run={run} compact />}
                                </div>
                            )
                        })}
                    </div>
                }
            </Panel>

            <Panel styles="w-full p-3 px-4 flex flex-col gap-3">
                <IconTitle title="Automation policy" icon={<VscRobot size={16}/>} />
                <p className="text-sm text-subtext2">
                    Fan and grouped grow lights can execute automatically after a passed safety check.
                    Pump, doser, water, and harvest recommendations stay advisory.
                </p>
                <p className="text-xs text-subtext3">
                    Current mappings: fan {POWERBOARD_DEVICE_IDS.fan}; grouped lights {POWERBOARD_DEVICE_IDS.lightLevel1} and {POWERBOARD_DEVICE_IDS.lightLevel2}.
                    There is no actuator-mapping API.
                </p>
                <Link to={PAGES.authPages.farmOverview} className="text-xs text-highlight hover:underline w-fit">
                    Open farm overview
                </Link>
            </Panel>
        </div>
    )
}
