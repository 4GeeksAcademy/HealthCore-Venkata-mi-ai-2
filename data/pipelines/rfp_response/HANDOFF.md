# RFP response handoff (Part 2 → Part 3)

Part 2 reads `rfp_ticket.handoff_json` when `status` is `intake_complete` and `handoff_ready` is true. It does not convert the PDF.

When Part 2 finishes, the same JSON is updated. `approval_status` stays empty.

```json
{
  "ticket_id": "uuid",
  "part": 2,
  "next": "part3_approval",
  "part2_outcome": "passed or needs_human_review",
  "evaluation_closed": true,
  "iteration_limit": 2,
  "status_trail": ["drafting", "under_evaluation"],
  "phi_detected": false,
  "part2_guard": "",
  "metadata": {},
  "conflicts": [],
  "sections": [
    {
      "department_id": "revenue",
      "owner_name": "Tom Callahan",
      "key_aspects": [],
      "draft_content": "",
      "review_state": "passed or needs_human_review",
      "provisional": false,
      "evaluation_result": {}
    }
  ]
}
```

Rules for Part 3:

- Do not treat `under_evaluation` plus `part2_outcome: passed` as `waiting_for_approval`. Part 2 does not set that status.
- `needs_human_review` means the iteration limit was exhausted or intake flagged patient information. The last draft (redacted if needed) and the `EvaluationResult` stay on the section. Do not drop the ticket.
- `conflicts[].resolution` is still `unresolved_for_part3`.
- `part2_guard` of `phi_review_required` means no draft was written. Claire Whitfield reviews first.
- A provisional section is not ready for Tom Callahan to send.

## Design answers

1. Each evaluator receives one section, that department's key aspects, and the shared metadata. It does not receive the PDF or the other drafts.
2. Evaluators return their slices. One parent write saves every `evaluation_results` value after the pools finish.
3. The backoffice names the owner and shows the feedback on a provisional draft. The ticket status is `needs_human_review`.
4. `feedback_for_generator` names the rule, the missing aspect, or the readability numbers.
