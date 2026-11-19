# RFP intake handoff (Part 1 → Part 2)

Part 2 starts from the ticket row. It does not convert the PDF again.

When `rfp_ticket.handoff_ready` is true and `status` is `intake_complete`, read `rfp_ticket.handoff_json`.

```json
{
  "ticket_id": "uuid",
  "part": 1,
  "next": "part2_drafting",
  "phi_detected": false,
  "part2_guard": "",
  "metadata": {
    "client_name": "",
    "client_country": "US or UK",
    "program_type": "",
    "covered_population": null,
    "deadline": "",
    "budget_range": "",
    "currency": "USD or GBP",
    "departments_needed": ["revenue", "clinical", "compliance"],
    "open_questions": []
  },
  "sections": [
    {
      "department_id": "revenue",
      "owner_name": "Tom Callahan",
      "owner_role": "Revenue Cycle Director",
      "key_aspects": [],
      "open_questions": [],
      "claims": {},
      "contains_phi": false
    }
  ],
  "conflicts": [],
  "sales_summary": "",
  "summary_source": "model or structured"
}
```

Rules for Part 2:

- `part2_guard` of `phi_review_required` means do not draft from the PDF or from any redacted span. Claire Whitfield reviews first.
- `conflicts[].resolution` stays `unresolved_for_part3`. Do not pick a winner in Part 2.
- Department ids are only `revenue`, `clinical`, and `compliance`.
- `approval_status` on `rfp_department_section` stays empty until Part 3.
- Part 2 writes `draft_content` and `evaluation_results`. Contract: `data/pipelines/rfp_response/HANDOFF.md`.
- A `discarded` or `failed` ticket has `handoff_ready` false. Do not draft it.
