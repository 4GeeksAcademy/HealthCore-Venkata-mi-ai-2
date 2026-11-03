# HealthCore Knowledge Base — Recall@3 Report

- Date: 2026-11-02
- Collection: `healthcore_knowledge`
- Embeddings model: `downtown-miami/openrouter/perplexity/pplx-embed-v1-0.6b` · Generation model: `downtown-miami/openrouter/openai/gpt-6-luna`
- `min_score` (cosine): **0.30**
- Questions: 16 (from `data/eval/test-queries.json`)

| Metric | Value | Target |
|--------|-------|--------|
| Recall@3 (ranking only) | **100%** | ≥ 80% |
| Recall@3 with `min_score` applied | **100%** | ≥ 80% |
| Lowest score of a correct chunk | 0.504 | > `min_score` |
| Highest top-1 score of an off-topic question | 0.105 | < `min_score` |

## Per question

| ID | Expected chunk | Rank | Score | Top 3 retrieved |
|----|----------------|------|-------|-----------------|
| Q01 | appointment-policy#1 | 1 | 0.636 | appointment-policy#1 (0.636)<br>appointment-policy#3 (0.386)<br>appointment-policy#2 (0.380) |
| Q02 | appointment-policy#1 | 1 | 0.544 | appointment-policy#1 (0.544)<br>appointment-policy#3 (0.466)<br>new-patient-checklist#2 (0.298) |
| Q03 | appointment-policy#0 | 1 | 0.656 | appointment-policy#0 (0.656)<br>appointment-policy#3 (0.477)<br>referral-process#2 (0.432) |
| Q04 | appointment-policy#2 | 1 | 0.674 | appointment-policy#2 (0.674)<br>appointment-policy#3 (0.416)<br>appointment-policy#1 (0.367) |
| Q05 | appointment-policy#3 | 1 | 0.576 | appointment-policy#3 (0.576)<br>appointment-policy#0 (0.503)<br>new-patient-checklist#2 (0.436) |
| Q06 | insurance-coverage#0 | 1 | 0.556 | insurance-coverage#0 (0.556)<br>new-patient-checklist#0 (0.258)<br>insurance-coverage#1 (0.257) |
| Q07 | insurance-coverage#0 | 1 | 0.504 | insurance-coverage#0 (0.504)<br>new-patient-checklist#2 (0.266)<br>new-patient-checklist#0 (0.251) |
| Q08 | insurance-coverage#1 | 1 | 0.644 | insurance-coverage#1 (0.644)<br>referral-process#0 (0.385)<br>insurance-coverage#0 (0.365) |
| Q09 | insurance-coverage#2 | 1 | 0.610 | insurance-coverage#2 (0.610)<br>insurance-coverage#1 (0.312)<br>new-patient-checklist#0 (0.311) |
| Q10 | new-patient-checklist#1 | 1 | 0.521 | new-patient-checklist#1 (0.521)<br>new-patient-checklist#0 (0.516)<br>new-patient-checklist#2 (0.302) |
| Q11 | new-patient-checklist#0 | 1 | 0.796 | new-patient-checklist#0 (0.796)<br>new-patient-checklist#2 (0.673)<br>new-patient-checklist#1 (0.640) |
| Q12 | new-patient-checklist#2 | 1 | 0.664 | new-patient-checklist#2 (0.664)<br>new-patient-checklist#0 (0.580)<br>new-patient-checklist#1 (0.404) |
| Q13 | referral-process#1 | 1 | 0.650 | referral-process#1 (0.650)<br>referral-process#2 (0.618)<br>referral-process#3 (0.612) |
| Q14 | referral-process#2 | 1 | 0.621 | referral-process#2 (0.621)<br>referral-process#0 (0.497)<br>referral-process#3 (0.480) |
| Q15 | referral-process#0 | 1 | 0.624 | referral-process#0 (0.624)<br>referral-process#3 (0.494)<br>referral-process#2 (0.413) |
| Q16 | referral-process#3 | 1 | 0.803 | referral-process#3 (0.803)<br>referral-process#0 (0.755)<br>referral-process#2 (0.471) |

## Off-topic questions (threshold check)

| ID | Top-1 chunk | Score | Clears `min_score`? |
|----|-------------|-------|---------------------|
| N01 | insurance-coverage#1 | 0.031 | no |
| N02 | insurance-coverage#0 | 0.086 | no |
| N03 | referral-process#1 | 0.105 | no |
| N04 | referral-process#0 | 0.087 | no |

## Sample generated answers (`query()`)

**Q:** Is there a charge for cancelling 12 hours in advance?

> Cancelling 12 hours in advance is less than 24 hours, so private-pay patients are charged 50 USD (or 40 GBP in the UK). Medicare or Medicaid patients are not charged a no-show fee, but the incident is logged in their record.
> 
> Source: appointment-policy › Cancellation policy

**Q:** What do I need to bring to my first appointment?

> Please bring:
> - A valid ID document.
> - Your insurance card, if applicable.
> - A list of current medications, if warranted by the reason for the visit.
> 
> Before your first appointment, complete the medical history form, identity verification, insurance coverage verification or self-pay confirmation, and the informed consent form for the clinic’s country. If the medical history form isn’t completed beforehand, you can still be seen, but the consultation time will be reduced.
> 
> Source: new-patient-checklist › Documents the patient should bring on the day of the appointment; New Patient Checklist

**Q:** Do you accept Humana?

> - **United States:** Humana is not on the documented list of accepted commercial insurers. Please verify with the billing team (Tom Callahan) before confirming anything to the patient.
> - **United Kingdom:** I don’t have documented UK coverage information for Humana. Please verify with the billing team (Tom Callahan) before confirming anything to the patient.
> 
> Source: insurance-coverage › United States (Texas, Florida, Georgia)

**Q:** A Medicaid patient missed their appointment without calling. Do we charge the no-show fee?

> No. Medicaid patients are not charged a no-show fee, but the incident is logged in their record.
> 
> Source: appointment-policy › Cancellation policy

**Q:** What is the Wi-Fi password for the staff network?

> I don't have enough information in the HealthCore knowledge base to answer that. Please check with the relevant team.

