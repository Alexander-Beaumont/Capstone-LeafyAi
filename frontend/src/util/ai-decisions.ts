import type { DecisionSeverity } from "../components/PendingDecisionCard"
import type { AIDecision } from "./types"
import { parseConfidence } from "./ai-agent"

export function decisionSeverity(score: string | number | null | undefined): DecisionSeverity {
    const value = parseConfidence(score)
    if (value == null || value < 0.4) return "Low"
    if (value < 0.7) return "Medium"
    return "High"
}

export function decisionName(decision: AIDecision) {
    return decision.decision_type || decision.category || "AI decision"
}
