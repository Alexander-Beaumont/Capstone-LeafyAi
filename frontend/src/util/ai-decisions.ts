import type { DecisionSeverity } from "../components/PendingDecisionCard"
import type { AIDecision } from "./types"

export function decisionSeverity(score: number | null): DecisionSeverity {
    if (score == null || score < 0.4) return "Low"
    if (score < 0.7) return "Medium"
    return "High"
}

export function decisionName(decision: AIDecision) {
    return decision.decision_type || decision.category || "AI decision"
}
