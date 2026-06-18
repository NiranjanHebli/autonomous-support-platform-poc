# LLM Red-Team Evaluation
## Cartly Support Copilot - KPI Critique via LLM-as-Staff-Engineer

**Author:** Niranjan Hebli & Bryson Gracias
**Date:** June 2026
**Purpose:** Use an LLM acting as a skeptical staff engineer to critique the PRD KPIs for measurability, gaming risk, and operational gaps.

---

## 1. Evaluation Setup

### Prompt Used

```
You are a skeptical senior staff engineer at a B2B SaaS company reviewing a product
requirements document for an AI support copilot. Your job is to identify which KPIs
are vague, hard to measure in practice, or likely to be gamed by a motivated team.
Be specific about what is wrong and suggest concrete revisions.

KPIs under review:
1. Retrieval Hit Rate >= 80%
2. Groundedness Rate >= 90%
3. Average Handle Time <= 10 minutes
4. Refund Safety Rate = 100%
5. Escalation Rate <= 15%
6. Answer Relevance Score >= 0.80 (RAGAS)
7. First Contact Resolution (FCR) >= 75%
8. Cost per Query < $0.002

For each KPI, answer: Is this measurable without ambiguity? What would break the measurement?
```

### Model Used
gpt-4o (reasoning model used for the critique pass, not the cheaper mini variant)

---

## 2. Model Response (Unedited)

**KPI 1 - Retrieval Hit Rate >= 80%**
Measurable, but requires a maintained golden evaluation set. Without a fixed, curated list of test questions with known correct chunks, "hit rate" is undefined. The risk: teams will cherry-pick easy queries for the eval set to inflate the number. Revision needed: define the golden set composition - minimum 20 questions, spanning all 5 intent categories, including adversarial phrasing variations. The golden set must be version-controlled and never modified to pass a failing metric.

**KPI 2 - Groundedness Rate >= 90%**
The core measurement challenge: who defines "grounded"? If you use the quality critic LLM itself to measure groundedness, you are grading your own homework. The critic may pass a response that a human reviewer would flag. Revision needed: monthly human audit sample - minimum 50 drafts reviewed by a human evaluator against the retrieved chunk. LLM-based critic is a production gate, not a measurement instrument.

**KPI 3 - Average Handle Time <= 10 minutes**
Measurable only if "handle time" is strictly defined. Is it ticket-open to agent-send? Or ticket-open to ticket-closed? If agents start closing tickets without sending (to game the clock), AHT will appear to drop while actual resolution quality degrades. Revision needed: define AHT as "ticket-open timestamp to agent-send timestamp, as recorded by the helpdesk system." Require FCR to be measured alongside AHT to prevent gaming.

**KPI 4 - Refund Safety Rate = 100%**
The right intent, but 100% is unmeasurable at zero occurrences without a denominator. "We had zero out-of-policy refunds" could mean the system never surfaced a refund draft at all. Revision needed: track "Refund Approval Drafts Presented" as a separate counter. Refund Safety Rate = (policy-compliant refund drafts) / (total refund drafts presented). Requires a policy compliance audit process.

**KPI 5 - Escalation Rate <= 15%**
Escalation definitions vary by team. If "escalation" means a Slack message to a supervisor, it will be measured differently than a formal ticket transfer. Revision needed: define escalation as a specific helpdesk action (e.g., ticket status set to "Escalated" in the system of record). Without a system-of-record definition, this metric is noise.

**KPI 6 - Answer Relevance Score >= 0.80 (RAGAS)**
RAGAS is a research framework - it requires a reference answer for comparison. Who writes the reference answers? If the team writes them, they will unconsciously bias them toward what the model produces. Revision needed: reference answers must be written by support policy owners (not the AI team) before the model is tested, and locked in version control.

**KPI 7 - First Contact Resolution (FCR) >= 75%**
FCR requires a definition of "resolved." If the customer does not reply within 48 hours, does that count as resolved? What if they re-open via a different channel? Revision needed: define FCR as "no customer re-contact on the same issue within 7 days via the same channel." Requires helpdesk system tracking.

**KPI 8 - Cost per Query < $0.002**
Measurable and the clearest KPI in this set. One risk: the cost model excludes infrastructure cost (compute, ChromaDB hosting, logging). Revision needed: define "cost per query" as fully-loaded API cost only (OpenAI tokens), with a separate infrastructure cost line item tracked monthly.

---

## 3. Engineer's Personal Critique of the Model's Response

The model's critique is largely valid and surfaces real production measurement gaps. The most critical observations are:

**Most important flag - KPI 2 (Groundedness):** The model correctly identifies the self-grading problem. Using the quality critic LLM to measure groundedness rate is circular. The production gate (critic blocking bad drafts) is sound, but the measurement instrument for the KPI must be a human audit sample, not the same model. This is a genuine flaw in the original PRD.

**Second most important - KPI 4 (Refund Safety):** The model is right that 100% is not a meaningful rate without a denominator. The revised definition (compliant drafts / total drafts presented) is operationally cleaner and actually measurable.

**Where the model is overly cautious:** The model's concern about KPI 8 (Cost per Query) adding infrastructure cost is reasonable but premature for V1. At the current scale, ChromaDB runs locally with zero hosting cost. The fully-loaded API-only cost is the right V1 measurement. Infrastructure cost becomes relevant at production scale, not during the de-risk phase.

---

## 4. Revised KPIs (Post Red-Team)

| KPI | Original Definition | Revised Definition |
|---|---|---|
| Retrieval Hit Rate | >= 80% | >= 80% on a version-controlled golden set of minimum 20 questions spanning all 5 intent categories, including adversarial phrasing. Golden set is never modified to pass a failing test. |
| Groundedness Rate | >= 90% (critic-measured) | >= 90% on monthly human audit sample (minimum 50 drafts). LLM critic is a production gate only, not the measurement instrument. |
| Average Handle Time | <= 10 minutes | Ticket-open to agent-send, as recorded by the helpdesk system. Must be measured alongside FCR to prevent gaming. |
| Refund Safety Rate | 100% | (Policy-compliant refund drafts) / (total refund drafts presented) = 100%. Requires policy compliance audit by support policy owner, not AI team. |
| Escalation Rate | <= 15% | Tickets with helpdesk status set to "Escalated" in system of record / total tickets processed by Copilot. |
| Answer Relevance Score | >= 0.80 RAGAS | >= 0.80 RAGAS against reference answers written by support policy owners before model testing, locked in version control. |
| FCR | >= 75% | No customer re-contact on the same issue within 7 days via the same channel. Requires helpdesk tracking. |
| Cost per Query | < $0.002 | Fully-loaded OpenAI API token cost per ticket. Infrastructure cost tracked separately as a monthly line item. |
