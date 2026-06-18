# Product Requirements Document (PRD)
## Cartly Support Copilot - v1.0

**Author:** Niranjan Hebli & Bryson Gracias
**Status:** Draft
**Last Updated:** June 2026
**Classification:** Internal - Sprint 0 Contract

---

## 1. Problem Statement

### 1.1 The Business Pain

Cartly, a mid-size B2B SaaS e-commerce platform, operates a human-staffed support team that manually answers product and policy questions by digging through scattered helpdesk wikis, changelog PDFs, and internal policy documents. This fragmented knowledge architecture creates three compounding operational failures:

#### Pain Point 1: High Handle Time

**Cartly's current average handle time (AHT) sits at approximately 15 minutes per ticket**, driven primarily by agents manually switching between 4-6 internal tabs to locate policy answers.

**Industry context:** A McKinsey & Company analysis found that knowledge workers spend an average of **1.8-2.5 hours per day** searching for and gathering information - equivalent to 20-30% of the entire workday (McKinsey Global Institute, The Social Economy, 2012; revalidated 2022). For support agents specifically, this friction is amplified during live customer interactions. The industry benchmark for B2B SaaS support is **7-10 minutes** per ticket for standard interactions (IrisAgent Industry Report, 2024; Kayako Benchmark Report, 2024), placing Cartly's 15-minute AHT at **50-100% above industry norm**.

**Before AI context:** In 2018-2020, before widespread AI/Copilot adoption, industry-reported AHT for B2B SaaS was already 10-14 minutes (Zendesk Benchmark Report, 2019). Cartly's current 15-minute figure reflects no meaningful improvement over the pre-AI baseline, which is the core operational gap this Copilot addresses.

#### Pain Point 2: Agent Ramp Time

New support agents at Cartly take **3-6 months** to reach confident, accurate policy recall. During this ramp period, they frequently escalate resolvable tickets, over-promise on refunds, or require supervisory review. Industry data confirms that new agents typically take **3-9 months** to reach full proficiency (LivePerson Agent Ramp Time Report, 2024), with the **60-90 day milestone** being the common contact center benchmark for new agent KPI attainment (AmplifAI Contact Center Benchmark, 2024).

#### Pain Point 3: Inconsistent Policy Answers

Because policy documents are not version-controlled or centrally surfaced, different agents give different answers to the same question. This creates **customer distrust, refund disputes, and escalation chains** that cost Cartly an estimated additional 20-30% in re-handle costs per affected ticket.

---

## 2. Proposed Solution

The Cartly Support Copilot is an AI-assisted agent tool that listens to an incoming support ticket, classifies the intent, retrieves the relevant policy clause from a ChromaDB vector store, and presents the support agent with a **grounded draft reply** for review before sending.

**Three-sentence summary:**

The Copilot is not an autonomous bot that replies to customers. It is an AI assistant that surfaces the right policy clause and drafts a policy-grounded reply in under 3 seconds, which the agent then reviews and sends. The agent retains full control and final approval over every customer message.

---

## 3. Users and Personas

| Persona | Role | Core Need |
|---|---|---|
| Support Agent | Primary user | Accurate, fast policy answers without tab-switching |
| Support Supervisor | Secondary user | Consistent quality, fewer escalations, audit trail |
| Ops Lead | Tertiary user | Cost visibility, performance metrics |

---

## 4. Scope

### In Scope: V1

- Intent classification of incoming support tickets (return, refund, shipping, account, product)
- Policy retrieval from ChromaDB using semantic search (text-embedding-3-small)
- Grounded draft reply generation via gpt-4o-mini
- Quality grounding critic (secondary LLM pass)
- Bounded action: Refund Approval Draft (agent-initiated, human-approved only)
- Source citation on every draft response
- Low-confidence fallback state (human-only mode when retrieval confidence is below threshold)
- PII masking before any external API call

### Out of Scope: V1

- Autonomous customer-facing replies without agent approval
- Multi-language support
- Actual money movement or refund execution
- CRM integrations (Zendesk, Salesforce)
- Voice channel support

---

## 5. Functional Requirements

| Req ID | Requirement | Priority |
|---|---|---|
| FR-01 | System must classify ticket intent with a confidence score | P0 |
| FR-02 | System must retrieve top-3 policy chunks from ChromaDB by cosine similarity | P0 |
| FR-03 | System must generate a draft response grounded in retrieved chunks only | P0 |
| FR-04 | System must cite the source chunk in every draft response | P0 |
| FR-05 | System must run a secondary quality critic to validate grounding before presenting draft | P0 |
| FR-06 | System must mask PII (name, email, order ID) before sending data to external APIs | P0 |
| FR-07 | When retrieval similarity score is below 0.6, system must present human-only fallback | P0 |
| FR-08 | Refund Approval Draft must require explicit agent click to confirm | P0 |
| FR-09 | System must return a draft within 3 seconds at P95 | P1 |
| FR-10 | All interactions must be logged with intent label, retrieved chunk IDs, and critic verdict | P1 |

---

## 6. Non-Functional Requirements

| Req ID | Requirement | Target |
|---|---|---|
| NFR-01 | P95 end-to-end latency | Less than 3 seconds |
| NFR-02 | Retrieval hit rate (correct chunk in top-3) | Greater than or equal to 80% |
| NFR-03 | Groundedness score (critic validates draft) | Greater than or equal to 90% |
| NFR-04 | PII leakage rate to external APIs | 0% - hard stop |
| NFR-05 | System availability (uptime) | Greater than or equal to 99.5% |
| NFR-06 | Cost per 1,000 queries | Less than $2.00 (see cost model in Technical Design) |

---

## 7. KPIs and Success Metrics

### Primary KPIs

| KPI | Definition | Current Baseline | Target (V1) | Do-Not-Ship Floor |
|---|---|---|---|---|
| **Average Handle Time (AHT)** | Mean time from ticket open to agent send | 15 minutes | Less than or equal to 10 minutes | No improvement or regression |
| **Retrieval Hit Rate** | % of queries where correct policy chunk is in top-3 results | Not measured | Greater than or equal to 80% | Below 75% - do not ship |
| **Groundedness Rate** | % of draft responses that the quality critic validates as grounded | Not measured | Greater than or equal to 90% | Below 85% - do not ship |
| **Answer Relevance Score** | Semantic similarity between draft response and the retrieved chunk | Not measured | Greater than or equal to 0.80 RAGAS score | Below 0.70 - do not ship |
| **Escalation Rate** | % of tickets that are escalated to a supervisor | ~25% (estimated) | Less than 15% | Above 20% in production |
| **Refund Safety Rate** | % of Refund Approval Drafts that are policy-compliant | Not measured | 100% | Any out-of-policy refund draft |
| **First Contact Resolution (FCR)** | % of tickets resolved without follow-up | ~65% (estimated) | Greater than or equal to 75% | Below 70% in production |
| **Cost per Query** | Blended API cost per ticket processed | Not measured | Less than $0.002 | Above $0.005 - escalate to architecture review |

### North-Star and Guardrail Pair (Tier A)

| Type | Metric | Rationale |
|---|---|---|
| **North-Star** | AHT Reduction (absolute minutes saved per ticket) | Directly maps to operational cost savings and agent productivity. Every minute saved at scale reduces headcount pressure. |
| **Guardrail** | Refund Safety Rate (must remain 100%) | A single out-of-policy refund approval can trigger legal risk or financial loss. This metric is non-negotiable and cannot be traded off against speed. |

### Metric Tree (Technical to Business)

```
Business KPI: AHT Reduction (15 min → ≤10 min)
│
├── Retrieval Hit Rate ≥80%
│       Ensures the correct policy chunk is surfaced - without this, the draft has nothing to ground on.
│
├── Groundedness Rate ≥90%
│       Ensures the draft does not hallucinate - directly affects agent trust and send rate.
│
├── P95 Latency <3s
│       Ensures the Copilot delivers results before the agent would have switched tabs manually.
│
└── Escalation Rate ≤15%
        Downstream effect of accurate retrieval and grounded drafts - reduces supervisor queue.
```

---

## 8. Appendix: Research Citations

| Claim | Source |
|---|---|
| Knowledge workers spend 1.8-2.5 hours/day searching for information | McKinsey Global Institute, The Social Economy (2012), revalidated in McKinsey Tech Benchmark Reports (2022) |
| B2B SaaS AHT benchmark: 7-10 minutes | IrisAgent Industry Benchmark Report (2024); Kayako AHT Benchmarks by Industry (2024) |
| 88% of service professionals say AI accelerates resolution times | Salesforce, State of Service, 6th Edition (2024) |
| AI agents report 20% average case resolution time decrease | Salesforce, State of Service, 6th Edition (2024) |
| New agents take 3-9 months to reach full proficiency | LivePerson Agent Ramp Time Report (2024) |
| 60-90 day milestone is the common contact center benchmark for new agent KPI attainment | AmplifAI Contact Center Benchmark (2024) |
| 66% of customers abandon brands after bad service, 73% switch after multiple bad experiences | CX industry surveys aggregated across Zendesk, Salesforce, and Qualtrics (2024) |
| AI copilot deployment reduced AHT by 14% at Catapult Sports | Zendesk Case Study: Catapult Sports (2024) |
| AI copilots save agents up to 82 minutes/day | Industry AI Efficiency Report (2024) |
| B2B SaaS cost per ticket: $30-$60 fully loaded | Lorikeet CX Report (2024); SupportBench Industry Report (2024) |
| Well-tuned RAG systems on domain-specific corpora achieve 80-90% retrieval hit rates | Vectara Hallucination Leaderboard (2024); RAGAS Benchmark Studies (2024) |
| FCR industry average: 70-79%; world-class: 80%+ | Zendesk, Hitachi Solutions, OpenSend benchmark aggregations (2024) |
| P95 latency for complex AI workflows: less than 4 seconds acceptable threshold | eachlabs.ai AI Latency Research (2024) |
Problem + Cost: Customer support agents are spending ~30% of their time manually reading and triaging inbound Social Media messages to the correct department (e.g., Billing, Tech Support, Refunds). This manual triage costs approximately $4,500/month in agent hours and delays first-response times by an average of 45 minutes.

Top 3 User Stories:

As a customer, I want my support query to reach the correct department immediately so that my issue is resolved faster.
As a support agent, I want incoming Social Media messages to be pre-categorized so that I only see tickets relevant to my expertise.
As a support manager, I want to see a confidence score for automated routing so I can review low-confidence categorization.
Scope:

In Scope: Categorization of English text messages from Social Media; predicting Category and Intent; filtering out low-confidence (<0.60) predictions.
Out of Scope: Voice/audio message classification; automated ticket resolution (bot replies); multi-lingual support.
Requirements:

Functional: Model must predict Intent and Category from a text string. The pipeline must fallback to 'UNDEFINED' if confidence is below 0.60.
Non-functional: Inference latency under 200ms per message. Model must run locally without cloud GPU dependencies.
KPIs:

Macro F1-Score: Harmonic mean of precision and recall across all intents. Target: >0.85. Floor: 0.75.
Intent Match Rate: Percentage of messages where predicted intent exactly matches human labels. Target: >90%. Floor: 80%.
p95 Latency: Time to run text through TF-IDF and LightGBM inference. Target: <50ms. Floor: <200ms.
Automated Route Rate (Business KPI): Percentage of inbound Social Media messages successfully categorized (Confidence > 0.60) without human intervention. Target: >75%. Floor: 60%.
