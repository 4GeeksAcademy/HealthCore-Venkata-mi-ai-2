import { validateCandidateInput, validateNoteContent } from "@/lib/validators";
import type { CandidateFormValues } from "@/types/candidate";

function validCandidate(): CandidateFormValues {
  return {
    fullName: "Alex Rivera",
    email: "alex.rivera@healthcore.example",
    phone: "555-0100",
    position: "Clinic Nurse",
    linkedinUrl: "https://linkedin.com/in/alex-rivera",
    cvUrl: "https://example.com/cv.pdf",
    experience: "5 years outpatient care",
    status: "received",
    stage: "pending",
    applicationDate: "2026-08-01",
  };
}

describe("validateCandidateInput", () => {
  test("accepts a complete hiring row", () => {
    const errors = validateCandidateInput(validCandidate());
    expect(errors).toEqual({});
  });

  test("rejects missing required fields and invalid URLs", () => {
    const errors = validateCandidateInput({
      ...validCandidate(),
      fullName: "   ",
      email: "not-an-email",
      position: "",
      applicationDate: "",
      linkedinUrl: "not-a-url",
      cvUrl: "also-bad",
      status: "received",
      stage: "pending",
    });

    expect(errors.fullName).toBe("Full name is required.");
    expect(errors.email).toBe("Enter a valid email address.");
    expect(errors.position).toBe("Position is required.");
    expect(errors.applicationDate).toBe("Application date is required.");
    expect(errors.linkedinUrl).toBe("Enter a valid LinkedIn URL.");
    expect(errors.cvUrl).toBe("Enter a valid CV URL.");
  });
});

describe("validateNoteContent", () => {
  test("accepts a non-empty note", () => {
    expect(validateNoteContent("Follow up after licence check.")).toBeNull();
  });

  test("rejects blank notes", () => {
    expect(validateNoteContent("   ")).toBe("Note content is required.");
    expect(validateNoteContent("")).toBe("Note content is required.");
  });
});
