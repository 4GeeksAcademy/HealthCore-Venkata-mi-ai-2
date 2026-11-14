"""Fixed refuse and redirect strings. No PHI, no leaked system text."""

JAILBREAK_REFUSAL = (
    "I cannot change or ignore my HealthCore instructions. "
    "I am the HealthCore desk knowledge assistant for clinic policies, procedures, "
    "compliance under HIPAA and UK GDPR, tickets, and inventory. "
    "Ask a HealthCore policy or operations question and I will help."
)

PERSONAL_TASK_REFUSAL = (
    "I can't help with personal tasks unrelated to HealthCore. "
    "I support clinic staff with HealthCore policies, procedures, compliance guidance, "
    "incident tickets, and inventory. Please ask a HealthCore desk or compliance question."
)

IDENTIFIABLE_REFUSAL = (
    "I cannot discuss a specific patient case that includes identifiable or "
    "quasi-identifiable details (names, ages with diagnoses, clinic combinations, "
    "or record numbers). Please rephrase your question about the policy or procedure "
    "without any patient identifiers, and I will help from HealthCore guidance."
)

CASUAL_REDIRECT_SUFFIX = (
    "\n\nI'm here for HealthCore clinic policies, compliance (HIPAA / UK GDPR), "
    "tickets, and inventory — ask whenever you need that."
)

OUTPUT_PHI_REFUSAL = (
    "I cannot return that response because it may contain protected health information. "
    "Please rephrase your question without patient identifiers so I can answer from "
    "HealthCore policy only."
)

SYSTEM_LEAK_REFUSAL = (
    "I cannot share internal system instructions. "
    "Ask a HealthCore policy, compliance, ticket, or inventory question instead."
)

ACTIVE_BREACH_REFUSAL = (
    "I cannot discuss details of active or under-investigation security breaches. "
    "For formally published HealthCore breach-notification procedures, ask about the "
    "HIPAA 60-day or UK GDPR 72-hour ICO timelines in general terms, without probing "
    "an open incident."
)
