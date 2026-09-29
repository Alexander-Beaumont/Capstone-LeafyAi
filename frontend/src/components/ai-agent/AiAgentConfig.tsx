import { useContext, useEffect, useMemo, useState } from "react"
import { AiAgentContext } from "../../providers/AiAgentProvider"
import { AI_PROVIDERS } from "../../util/constants"
import { toApiTime, toInputTime, validateAiSettings } from "../../util/ai-agent"
import type { AIProviderName, ProviderTestRole } from "../../util/types"
import Button from "../primatives/Button"
import Dropdown, { type dataFormat } from "../primatives/Dropdown"
import Switch from "../primatives/Switch"
import TextBox from "../primatives/Textbox"

const providerItems: dataFormat[] = AI_PROVIDERS.map((name, id) => ({ id, name }))

function providerItem(name: string) {
    return providerItems.find(item => item.name === name) ?? providerItems[0]
}

export default function AiAgentConfig() {
    const ai = useContext(AiAgentContext)
    const settings = ai.settings

    const [llmProvider, setLlmProvider] = useState<AIProviderName>("mock")
    const [llmModel, setLlmModel] = useState("")
    const [llmKey, setLlmKey] = useState("")
    const [clearLlmKey, setClearLlmKey] = useState(false)
    const [vlmProvider, setVlmProvider] = useState<AIProviderName>("mock")
    const [vlmModel, setVlmModel] = useState("")
    const [vlmKey, setVlmKey] = useState("")
    const [clearVlmKey, setClearVlmKey] = useState(false)
    const [scheduleEnabled, setScheduleEnabled] = useState(false)
    const [intervalMinutes, setIntervalMinutes] = useState("30")
    const [activeStartTime, setActiveStartTime] = useState("08:00")
    const [activeEndTime, setActiveEndTime] = useState("20:00")
    const [maxImages, setMaxImages] = useState("4")
    const [maxImageAge, setMaxImageAge] = useState("60")
    const [testMessage, setTestMessage] = useState("")
    const [testError, setTestError] = useState("")
    const [saveMessage, setSaveMessage] = useState("")

    useEffect(() => {
        if (!settings) return
        setLlmProvider(settings.llm_provider)
        setLlmModel(settings.llm_model)
        setLlmKey("")
        setClearLlmKey(false)
        setVlmProvider(settings.vlm_provider)
        setVlmModel(settings.vlm_model)
        setVlmKey("")
        setClearVlmKey(false)
        setScheduleEnabled(settings.schedule_enabled)
        setIntervalMinutes(String(settings.interval_minutes))
        setActiveStartTime(toInputTime(settings.active_start_time))
        setActiveEndTime(toInputTime(settings.active_end_time))
        setMaxImages(String(settings.max_images))
        setMaxImageAge(String(settings.max_image_age_minutes))
    }, [settings])

    const errors = useMemo(() => validateAiSettings({
        scheduleEnabled,
        intervalMinutes,
        maxImages,
        maxImageAge,
        activeStartTime,
        activeEndTime,
    }), [scheduleEnabled, intervalMinutes, maxImages, maxImageAge, activeStartTime, activeEndTime])

    const dirty = Boolean(settings) && (
        llmProvider !== settings?.llm_provider
        || llmModel !== settings?.llm_model
        || vlmProvider !== settings?.vlm_provider
        || vlmModel !== settings?.vlm_model
        || scheduleEnabled !== settings?.schedule_enabled
        || (scheduleEnabled && (
            Number(intervalMinutes) !== settings?.interval_minutes
            || toApiTime(activeStartTime) !== toApiTime(settings?.active_start_time ?? "")
            || toApiTime(activeEndTime) !== toApiTime(settings?.active_end_time ?? "")
            || Number(maxImages) !== settings?.max_images
        ))
        || Number(maxImageAge) !== settings?.max_image_age_minutes
        || llmKey.trim() !== ""
        || vlmKey.trim() !== ""
        || clearLlmKey
        || clearVlmKey
    )

    async function save() {
        if (!settings || Object.keys(errors).length || !dirty) return
        const patch: Parameters<typeof ai.saveSettings>[0] = {}
        if (llmProvider !== settings.llm_provider) patch.llm_provider = llmProvider
        if (llmModel !== settings.llm_model) patch.llm_model = llmModel
        if (vlmProvider !== settings.vlm_provider) patch.vlm_provider = vlmProvider
        if (vlmModel !== settings.vlm_model) patch.vlm_model = vlmModel
        if (scheduleEnabled !== settings.schedule_enabled) patch.schedule_enabled = scheduleEnabled
        if (scheduleEnabled) {
            if (Number(intervalMinutes) !== settings.interval_minutes) patch.interval_minutes = Number(intervalMinutes)
            if (toApiTime(activeStartTime) !== toApiTime(settings.active_start_time)) patch.active_start_time = toApiTime(activeStartTime)
            if (toApiTime(activeEndTime) !== toApiTime(settings.active_end_time)) patch.active_end_time = toApiTime(activeEndTime)
            if (Number(maxImages) !== settings.max_images) patch.max_images = Number(maxImages)
        }
        if (Number(maxImageAge) !== settings.max_image_age_minutes) patch.max_image_age_minutes = Number(maxImageAge)
        if (clearLlmKey) patch.clear_llm_api_key = true
        else if (llmKey.trim()) patch.llm_api_key = llmKey.trim()
        if (clearVlmKey) patch.clear_vlm_api_key = true
        else if (vlmKey.trim()) patch.vlm_api_key = vlmKey.trim()

        const result = await ai.saveSettings(patch)
        if (result.success) {
            setLlmKey("")
            setVlmKey("")
            setSaveMessage("Settings saved.")
        } else {
            setSaveMessage("")
        }
    }

    async function runTest(role: ProviderTestRole) {
        setTestMessage("")
        setTestError("")
        const result = await ai.testProvider(role)
        if (!result.success || result.data?.success === false) {
            const failures = result.data?.failures?.join(" ")
            setTestError(result.data?.detail || result.msg || failures || "Provider test failed.")
            return
        }
        const data = result.data
        setTestMessage(`${data?.provider ?? role} / ${data?.model ?? "unknown"}: ${data?.response ?? "OK"}`)
    }

    if (!settings && ai.loading) {
        return <div className="h-40 bg-panel2 animate-pulse rounded-md" />
    }

    return (
        <div className="flex flex-col gap-5">
            <div className="grid gap-4 md:grid-cols-2">
                <div className="flex flex-col gap-3">
                    <p className="text-sm text-subtext1 font-semibold">LLM</p>
                    <Dropdown
                        items={providerItems}
                        selectedItem={providerItem(llmProvider)}
                        setSelectedItem={id => setLlmProvider(providerItems[id].name as AIProviderName)}
                        showIcon
                    />
                    <TextBox
                        name="LLM model"
                        value={llmModel}
                        setValue={setLlmModel}
                        charLimit={255}
                        placeHolder="model name"
                    />
                    <TextBox
                        name="Replacement LLM API key"
                        value={llmKey}
                        setValue={value => {
                            setLlmKey(value)
                            if (value) setClearLlmKey(false)
                        }}
                        charLimit={255}
                        placeHolder={settings?.llm_api_key_configured ? "Leave blank to keep stored key" : "Optional"}
                        password
                    />
                    {settings?.llm_api_key_configured ?
                        <>
                            <p className="text-xs text-subtext3">Stored key {settings.llm_api_key_mask}</p>
                            <Button
                                name="Clear stored LLM key"
                                highlight={false}
                                onSubmit={() => {
                                    setClearLlmKey(true)
                                    setLlmKey("")
                                }}
                            />
                        </>
                    : <p className="text-xs text-subtext3">No LLM key stored.</p>}
                </div>
                <div className="flex flex-col gap-3">
                    <p className="text-sm text-subtext1 font-semibold">VLM</p>
                    <Dropdown
                        items={providerItems}
                        selectedItem={providerItem(vlmProvider)}
                        setSelectedItem={id => setVlmProvider(providerItems[id].name as AIProviderName)}
                        showIcon
                    />
                    <TextBox
                        name="VLM model"
                        value={vlmModel}
                        setValue={setVlmModel}
                        charLimit={255}
                        placeHolder="model name"
                    />
                    <TextBox
                        name="Replacement VLM API key"
                        value={vlmKey}
                        setValue={value => {
                            setVlmKey(value)
                            if (value) setClearVlmKey(false)
                        }}
                        charLimit={255}
                        placeHolder={settings?.vlm_api_key_configured ? "Leave blank to keep stored key" : "Optional"}
                        password
                    />
                    {settings?.vlm_api_key_configured ?
                        <>
                            <p className="text-xs text-subtext3">Stored key {settings.vlm_api_key_mask}</p>
                            <Button
                                name="Clear stored VLM key"
                                highlight={false}
                                onSubmit={() => {
                                    setClearVlmKey(true)
                                    setVlmKey("")
                                }}
                            />
                        </>
                    : <p className="text-xs text-subtext3">No VLM key stored.</p>}
                </div>
            </div>

            <TextBox
                name="Maximum image age (minutes)"
                value={maxImageAge}
                setValue={setMaxImageAge}
                charLimit={5}
                placeHolder="60"
                numeric
                invalidFunc={() => Boolean(errors.maxImageAge)}
            />

            <div className="flex items-center justify-between bg-panel2 border border-border rounded-lg p-3">
                <p className="text-sm text-subtext1">Schedule enabled</p>
                <Switch ticked={scheduleEnabled} setTicked={setScheduleEnabled} />
            </div>

            {scheduleEnabled ?
                <div className="grid gap-4 md:grid-cols-2">
                    <TextBox
                        name="Frequency (minutes)"
                        value={intervalMinutes}
                        setValue={setIntervalMinutes}
                        charLimit={4}
                        placeHolder="30"
                        numeric
                        invalidFunc={() => Boolean(errors.intervalMinutes)}
                    />
                    <TextBox
                        name="Maximum images"
                        value={maxImages}
                        setValue={setMaxImages}
                        charLimit={1}
                        placeHolder="4"
                        numeric
                        invalidFunc={() => Boolean(errors.maxImages)}
                    />
                    <TextBox
                        name="Active start"
                        value={activeStartTime}
                        setValue={setActiveStartTime}
                        charLimit={5}
                        placeHolder="08:00"
                        invalidFunc={() => Boolean(errors.activeStartTime)}
                    />
                    <TextBox
                        name="Active end"
                        value={activeEndTime}
                        setValue={setActiveEndTime}
                        charLimit={5}
                        placeHolder="08:00"
                        invalidFunc={() => Boolean(errors.activeEndTime)}
                    />
                </div>
            : null}

            {Object.values(errors).map(message => (
                <p key={message} className="text-xs text-high">{message}</p>
            ))}
            {ai.settingsError ? <p className="text-xs text-high">{ai.settingsError}</p> : null}
            {saveMessage ? <p className="text-xs text-low">{saveMessage}</p> : null}

            <div className="flex flex-wrap gap-3">
                <Button
                    name="Save settings"
                    highlight
                    loading={ai.saving}
                    onSubmit={save}
                />
                <Button
                    name="Test LLM"
                    highlight={false}
                    loading={ai.testingRole === "llm"}
                    onSubmit={() => runTest("llm")}
                />
                <Button
                    name="Test VLM"
                    highlight={false}
                    loading={ai.testingRole === "vlm"}
                    onSubmit={() => runTest("vlm")}
                />
            </div>
            {testMessage ? <p className="text-xs text-low break-all">{testMessage}</p> : null}
            {testError ? <p className="text-xs text-high">{testError}</p> : null}
        </div>
    )
}
