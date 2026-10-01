# Agent Office Decisions

## Decision 1: Backend remains the source of runtime truth

**Decision**  
Keep state inference, arbitration, and lifecycle ownership in the backend. The frontend continues to map normalized state to spatial behavior.

**Reason**  
Provider-specific and heuristic evidence must be reconciled once. Duplicating inference in the frontend would make behavior inconsistent and harder to test.

**Rejected alternatives**
- Let the frontend infer status from raw events.
- Send provider-specific Codex events directly into PixiJS.

---

## Decision 2: Add explicit event provenance

**Decision**  
Every normalized AgentEvent should carry a provider-agnostic source/provenance field with a backward-compatible default.

**Reason**  
The runtime currently mixes wrapper events, process scans, child-process tool observations, and timeout heuristics. Without provenance, the runtime cannot distinguish trusted facts from fallback inference.

**Rejected alternatives**
- Keep source only in payload metadata.
- Infer source from event type.
- Let “last writer wins” remain the arbitration model.

---

## Decision 3: Use source precedence plus recency

**Decision**  
Centralize a source-priority policy and combine it with timestamps when accepting status changes.

Initial precedence:
native > wrapper > tool_process > filesystem > git > process > timeout.

**Reason**  
High-confidence evidence should dominate lower-confidence heuristics, while stale evidence should not overwrite newer evidence of comparable authority.

**Rejected alternatives**
- Pure confidence scores distributed across observers.
- Pure timestamp ordering.
- Hard-coded if/else checks in each observer.

---

## Decision 4: office-run owns wrapped-agent identity

**Decision**  
When AGENT_OFFICE_ID exists, the wrapped identity is authoritative. Passive process discovery is fallback detection and must not create a second visible agent for the same wrapped process.

**Reason**  
office-run has explicit identity, repository, role, task, and lifecycle context that generic process scanning cannot reliably reconstruct.

**Rejected alternatives**
- Treat wrapper and passive discovery as equal independent agents.
- Disable passive scanning entirely.

---

## Decision 5: Keep current WebSocket shape compatible

**Decision**  
Preserve snapshot / agent.started / agent.updated / agent.stopped as the frontend protocol.

**Reason**  
The current frontend architecture is already clean and functional. This phase targets state fidelity, not protocol churn.

**Rejected alternatives**
- Replace the protocol with raw event streaming.
- Rebuild the frontend around provider-specific event streams.

---

## Decision 6: No broad UI redesign in this phase

**Decision**  
Do not spend this phase on new rooms, sprites, or layout systems. Minimal diagnostic exposure of provenance is acceptable.

**Reason**  
The current limiting factor is correctness of state interpretation, not visual capability.

**Rejected alternatives**
- Prioritize visual polish before improving runtime fidelity.
