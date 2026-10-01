import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from "react"
import {
    generateFarmRecommendations,
    getAiFarmSettings,
    getLatestRecommendations,
    getRecentRecommendations,
    patchAiFarmSettings,
    testAiProvider,
} from "../util/api-service-layer"
import { AI_AGENT_POLL_MS } from "../util/constants"
import type {
    AIConfiguration,
    AIConfigurationPatch,
    APIResult,
    ProviderTestResult,
    ProviderTestRole,
    RecommendationRun,
} from "../util/types"
import { FarmOverviewContext } from "./FarmOverviewProvider"
import { userContext } from "./UserProvider"

interface AiAgentType {
    settings: AIConfiguration | null
    latestRun: RecommendationRun | null
    recentRuns: RecommendationRun[]
    loading: boolean
    generating: boolean
    saving: boolean
    testingRole: ProviderTestRole | null
    generateError: string
    settingsError: string
    runsError: string
    generateNow: () => Promise<boolean>
    saveSettings: (patch: AIConfigurationPatch) => Promise<APIResult<AIConfiguration>>
    testProvider: (role: ProviderTestRole) => Promise<APIResult<ProviderTestResult>>
    refresh: () => void
}

const initialValues: AiAgentType = {
    settings: null,
    latestRun: null,
    recentRuns: [],
    loading: false,
    generating: false,
    saving: false,
    testingRole: null,
    generateError: "",
    settingsError: "",
    runsError: "",
    generateNow: async () => false,
    saveSettings: async () => ({ success: false, msg: "Not ready" }),
    testProvider: async () => ({ success: false, msg: "Not ready" }),
    refresh: () => null,
}

export const AiAgentContext = createContext<AiAgentType>(initialValues)

interface Props {
    children: ReactNode
}

export default function AiAgentProvider({ children }: Props) {
    const user = useContext(userContext)
    const { farmId } = useContext(FarmOverviewContext)
    const [settings, setSettings] = useState<AIConfiguration | null>(null)
    const [latestRun, setLatestRun] = useState<RecommendationRun | null>(null)
    const [recentRuns, setRecentRuns] = useState<RecommendationRun[]>([])
    const [loading, setLoading] = useState(false)
    const [generating, setGenerating] = useState(false)
    const [saving, setSaving] = useState(false)
    const [testingRole, setTestingRole] = useState<ProviderTestRole | null>(null)
    const [generateError, setGenerateError] = useState("")
    const [settingsError, setSettingsError] = useState("")
    const [runsError, setRunsError] = useState("")
    const [update, setUpdate] = useState(0)

    const loadSettings = useCallback(async () => {
        if (!user.accessToken || farmId == null) return
        const result = await getAiFarmSettings(user.accessToken, farmId)
        if (!result.success) {
            setSettingsError(result.msg)
            return
        }
        setSettingsError("")
        setSettings(result.data ?? null)
    }, [farmId, user.accessToken])

    const loadRuns = useCallback(async () => {
        if (!user.accessToken || farmId == null) return
        const [latest, recent] = await Promise.all([
            getLatestRecommendations(user.accessToken, farmId),
            getRecentRecommendations(user.accessToken, farmId),
        ])
        if (!latest.success) {
            setRunsError(latest.msg)
        } else {
            setLatestRun(latest.data ?? null)
        }
        if (!recent.success) {
            setRunsError(recent.msg)
        } else {
            setRecentRuns(recent.data ?? [])
            if (latest.success) setRunsError("")
        }
    }, [farmId, user.accessToken])

    useEffect(() => {
        if (!user.loggedIn || !user.accessToken || farmId == null) return
        let cancelled = false
        const run = async () => {
            setLoading(true)
            try {
                await Promise.all([loadSettings(), loadRuns()])
            } finally {
                if (!cancelled) setLoading(false)
            }
        }
        run()
        return () => {
            cancelled = true
        }
    }, [farmId, user.loggedIn, user.accessToken, update, loadSettings, loadRuns])

    // Recommendation history is polled only while a farm is selected. Hidden
    // browser tabs avoid unnecessary refresh traffic until visible again.
    useEffect(() => {
        if (!user.loggedIn || !user.accessToken || farmId == null) return
        let cancelled = false
        let timeout: ReturnType<typeof setTimeout> | undefined

        const tick = async () => {
            if (document.visibilityState === "visible") {
                await loadRuns()
            }
            if (!cancelled) timeout = setTimeout(tick, AI_AGENT_POLL_MS)
        }

        const onVisibility = () => {
            if (document.visibilityState === "visible") loadRuns()
        }

        timeout = setTimeout(tick, AI_AGENT_POLL_MS)
        document.addEventListener("visibilitychange", onVisibility)
        return () => {
            cancelled = true
            if (timeout) clearTimeout(timeout)
            document.removeEventListener("visibilitychange", onVisibility)
        }
    }, [farmId, user.loggedIn, user.accessToken, loadRuns])

    const generateNow = useCallback(async () => {
        if (!user.accessToken || farmId == null || generating) return false
        setGenerating(true)
        setGenerateError("")
        try {
            const result = await generateFarmRecommendations(user.accessToken, farmId)
            if (!result.success) {
                setGenerateError(result.msg)
                if (result.data) setLatestRun(result.data)
                await loadRuns()
                return false
            }
            await loadRuns()
            return true
        } finally {
            setGenerating(false)
        }
    }, [farmId, generating, loadRuns, user.accessToken])

    const saveSettings = useCallback(async (patch: AIConfigurationPatch) => {
        if (!user.accessToken || farmId == null) {
            return { success: false, msg: "Farm is not ready" } as const
        }
        setSaving(true)
        try {
            const result = await patchAiFarmSettings(user.accessToken, farmId, patch)
            if (!result.success) {
                setSettingsError(result.msg)
                return result
            }
            setSettingsError("")
            setSettings(result.data ?? null)
            return result
        } finally {
            setSaving(false)
        }
    }, [farmId, user.accessToken])

    const testProvider = useCallback(async (role: ProviderTestRole) => {
        if (!user.accessToken || farmId == null) {
            return { success: false, msg: "Farm is not ready" } as const
        }
        setTestingRole(role)
        try {
            return await testAiProvider(user.accessToken, farmId, role)
        } finally {
            setTestingRole(null)
        }
    }, [farmId, user.accessToken])

    return (
        <AiAgentContext.Provider
            value={{
                settings,
                latestRun,
                recentRuns,
                loading,
                generating,
                saving,
                testingRole,
                generateError,
                settingsError,
                runsError,
                generateNow,
                saveSettings,
                testProvider,
                refresh: () => setUpdate(Math.random()),
            }}
        >
            {children}
        </AiAgentContext.Provider>
    )
}
