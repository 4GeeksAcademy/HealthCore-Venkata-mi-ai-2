import test, { type TestContext } from "node:test";
import assert from "node:assert/strict";

import {
	Appointment,
	Claim,
	Clinician,
	Location,
	binarySearchClaimById,
	calculateDenialRate,
	calculateNoShowCost,
	denialRateByLocation,
	denialRateByPayer,
	filterClaims,
	findClaimById,
	findClinicianById,
	flagHighDenialPayers,
	flagHighNoShowLocations,
	generateCMEReport,
	getCliniciansAtRisk,
	getCliniciansWithExpiringLicences,
	groupClaimsBy,
	noShowRateByLocation,
	sortClaimsById,
	validateClaim,
	validateClinician,
} from "../index";

const sampleLocations: Location[] = [
	{
		locationId: "us-tx-001",
		name: "HealthCore Austin Central",
		city: "Austin",
		stateOrCountry: "TX",
		country: "US",
		phone: "(512) 340-8800",
		averageConsultationFee: {
			primary_care: 180,
			chronic_disease: 220,
			preventive: 150,
			specialist: 320,
			womens_health: 240,
			paediatric: 175,
			mental_health: 200,
		},
	},
	{
		locationId: "us-fl-001",
		name: "HealthCore Miami",
		city: "Miami",
		stateOrCountry: "FL",
		country: "US",
		phone: "(305) 510-7700",
		averageConsultationFee: {
			primary_care: 195,
			chronic_disease: 235,
			preventive: 160,
			specialist: 340,
			womens_health: 255,
			paediatric: 185,
			mental_health: 215,
		},
	},
	{
		locationId: "us-ga-001",
		name: "HealthCore Atlanta",
		city: "Atlanta",
		stateOrCountry: "GA",
		country: "US",
		phone: "(404) 330-9900",
		averageConsultationFee: {
			primary_care: 170,
			chronic_disease: 210,
			preventive: 145,
			specialist: 310,
			womens_health: 230,
			paediatric: 165,
			mental_health: 190,
		},
	},
];

const sampleClaims: Claim[] = [
	{
		claimId: "CLM-000001",
		patientId: "HC-A3F291",
		locationId: "us-tx-001",
		serviceType: "primary_care",
		payerName: "BlueCross",
		payerId: "BC001",
		submissionDate: "2025-03-10",
		claimAmount: 180,
		status: "approved",
		resubmitted: false,
	},
	{
		claimId: "CLM-000002",
		patientId: "HC-B7K442",
		locationId: "us-fl-001",
		serviceType: "specialist",
		payerName: "Aetna",
		payerId: "AET002",
		submissionDate: "2025-03-11",
		claimAmount: 340,
		status: "denied",
		denialReason: "missing_authorisation",
		resubmitted: false,
	},
	{
		claimId: "CLM-000003",
		patientId: "HC-C2M881",
		locationId: "us-ga-001",
		serviceType: "chronic_disease",
		payerName: "Medicare",
		payerId: "MED003",
		submissionDate: "2025-03-12",
		claimAmount: 210,
		status: "approved",
		resubmitted: false,
	},
	{
		claimId: "CLM-000004",
		patientId: "HC-D9P553",
		locationId: "us-tx-001",
		serviceType: "preventive",
		payerName: "BlueCross",
		payerId: "BC001",
		submissionDate: "2025-03-13",
		claimAmount: 150,
		status: "denied",
		denialReason: "coding_error",
		resubmitted: true,
	},
	{
		claimId: "CLM-000005",
		patientId: "HC-E4Q117",
		locationId: "us-fl-001",
		serviceType: "mental_health",
		payerName: "Cigna",
		payerId: "CIG004",
		submissionDate: "2025-03-14",
		claimAmount: 215,
		status: "pending",
		resubmitted: false,
	},
];

const sampleAppointments: Appointment[] = [
	{
		appointmentId: "APT-000001",
		patientId: "HC-A3F291",
		locationId: "us-tx-001",
		serviceType: "primary_care",
		scheduledDate: "2025-03-10",
		scheduledTime: "09:00",
		status: "completed",
		confirmedAt: "2025-03-09T14:00:00Z",
	},
	{
		appointmentId: "APT-000002",
		patientId: "HC-F6R228",
		locationId: "us-fl-001",
		serviceType: "specialist",
		scheduledDate: "2025-03-11",
		scheduledTime: "11:30",
		status: "no_show",
	},
	{
		appointmentId: "APT-000003",
		patientId: "HC-G1S774",
		locationId: "us-tx-001",
		serviceType: "chronic_disease",
		scheduledDate: "2025-03-12",
		scheduledTime: "14:00",
		status: "no_show",
	},
	{
		appointmentId: "APT-000004",
		patientId: "HC-H8T390",
		locationId: "us-ga-001",
		serviceType: "preventive",
		scheduledDate: "2025-03-13",
		scheduledTime: "10:00",
		status: "completed",
		confirmedAt: "2025-03-12T09:30:00Z",
	},
	{
		appointmentId: "APT-000005",
		patientId: "HC-I5U661",
		locationId: "us-fl-001",
		serviceType: "mental_health",
		scheduledDate: "2025-03-14",
		scheduledTime: "16:00",
		status: "no_show",
	},
];

const sampleClinicians: Clinician[] = [
	{
		clinicianId: "CLN-000001",
		firstName: "Marcus",
		lastName: "Reid",
		role: "physician",
		locationId: "us-tx-001",
		licenceState: "TX",
		licenceExpiryDate: "2026-06-30",
		cmeHoursRequired: 40,
		cmeHoursLogged: 28,
		cmeYearStartDate: "2025-01-01",
	},
	{
		clinicianId: "CLN-000002",
		firstName: "Sandra",
		lastName: "Flores",
		role: "nurse_practitioner",
		locationId: "us-fl-001",
		licenceState: "FL",
		licenceExpiryDate: "2025-05-15",
		cmeHoursRequired: 30,
		cmeHoursLogged: 6,
		cmeYearStartDate: "2025-01-01",
	},
	{
		clinicianId: "CLN-000003",
		firstName: "David",
		lastName: "Okafor",
		role: "physician",
		locationId: "us-ga-001",
		licenceState: "GA",
		licenceExpiryDate: "2027-01-01",
		cmeHoursRequired: 40,
		cmeHoursLogged: 40,
		cmeYearStartDate: "2025-01-01",
	},
];

function stepLog(step: string, actual: unknown, expected: unknown): void {
	console.log(
		`[STEP] ${step}\n  actual: ${JSON.stringify(actual)}\n  expected: ${JSON.stringify(expected)}`
	);
}

test("transformations return expected rates and costs", async (t: TestContext) => {
	await t.test("1) calculateDenialRate returns 40", () => {
		const actual = calculateDenialRate(sampleClaims);
		const expected = 40;
		stepLog("calculateDenialRate(sampleClaims)", actual, expected);
		assert.equal(actual, expected);
	});

	await t.test("2) denialRateByPayer returns expected distribution", () => {
		const actual = denialRateByPayer(sampleClaims);
		const expected = {
			BlueCross: 50,
			Aetna: 100,
			Medicare: 0,
			Cigna: 0,
		};
		stepLog("denialRateByPayer(sampleClaims)", actual, expected);
		assert.deepEqual(actual, expected);
	});

	await t.test("3) denialRateByLocation returns expected distribution", () => {
		const actual = denialRateByLocation(sampleClaims);
		const expected = {
			"us-tx-001": 50,
			"us-fl-001": 50,
			"us-ga-001": 0,
		};
		stepLog("denialRateByLocation(sampleClaims)", actual, expected);
		assert.deepEqual(actual, expected);
	});

	await t.test("4) flagHighDenialPayers returns payers over threshold", () => {
		const actual = flagHighDenialPayers(sampleClaims);
		const expected = ["BlueCross", "Aetna"];
		stepLog("flagHighDenialPayers(sampleClaims)", actual, expected);
		assert.deepEqual(actual, expected);
	});

	await t.test("5) calculateNoShowCost computes Miami week cost", () => {
		const actual = calculateNoShowCost(sampleAppointments, sampleLocations[1], "2025-03-14");
		const expected = 555;
		stepLog("calculateNoShowCost(Miami, weekEnding=2025-03-14)", actual, expected);
		assert.equal(actual, expected);
	});

	await t.test("6) noShowRateByLocation returns expected rates", () => {
		const actual = noShowRateByLocation(sampleAppointments);
		const expected = {
			"us-tx-001": 50,
			"us-fl-001": 100,
			"us-ga-001": 0,
		};
		stepLog("noShowRateByLocation(sampleAppointments)", actual, expected);
		assert.deepEqual(actual, expected);
	});

	await t.test("7) flagHighNoShowLocations returns locations over threshold", () => {
		const actual = flagHighNoShowLocations(sampleAppointments);
		const expected = ["us-tx-001", "us-fl-001"];
		stepLog("flagHighNoShowLocations(sampleAppointments)", actual, expected);
		assert.deepEqual(actual, expected);
	});
});

test("collections and search helpers return expected results", async (t: TestContext) => {
	await t.test("1) filterClaims finds denied claims", () => {
		const actual = filterClaims(sampleClaims, { status: "denied" }).map((claim) => claim.claimId);
		const expected = ["CLM-000002", "CLM-000004"];
		stepLog("filterClaims(status=denied)", actual, expected);
		assert.deepEqual(actual, expected);
	});

	await t.test("2) groupClaimsBy groups by payerName", () => {
		const grouped = groupClaimsBy(sampleClaims, "payerName");
		const actual = Object.keys(grouped);
		const expected = ["BlueCross", "Aetna", "Medicare", "Cigna"];
		stepLog("Object.keys(groupClaimsBy(..., payerName))", actual, expected);
		assert.deepEqual(actual, expected);
		assert.equal(grouped.BlueCross.length, 2, "BlueCross should have 2 claims");
	});

	await t.test("3) sortClaimsById returns ascending ids", () => {
		const actual = sortClaimsById(sampleClaims, "asc").map((claim) => claim.claimId);
		const expected = [
			"CLM-000001",
			"CLM-000002",
			"CLM-000003",
			"CLM-000004",
			"CLM-000005",
		];
		stepLog("sortClaimsById(sampleClaims, asc)", actual, expected);
		assert.deepEqual(actual, expected);
	});

	await t.test("4) findClaimById finds CLM-000003", () => {
		const actual = findClaimById(sampleClaims, "CLM-000003")?.payerName;
		const expected = "Medicare";
		stepLog("findClaimById(..., CLM-000003)?.payerName", actual, expected);
		assert.equal(actual, expected);
	});

	await t.test("5) findClinicianById finds CLN-000002", () => {
		const actual = findClinicianById(sampleClinicians, "CLN-000002")?.firstName;
		const expected = "Sandra";
		stepLog("findClinicianById(..., CLN-000002)?.firstName", actual, expected);
		assert.equal(actual, expected);
	});

	await t.test("6) binarySearchClaimById returns index 3 for CLM-000004", () => {
		const sorted = sortClaimsById(sampleClaims, "asc");
		const actual = binarySearchClaimById(sorted, "CLM-000004");
		const expected = 3;
		stepLog("binarySearchClaimById(sortedClaims, CLM-000004)", actual, expected);
		assert.equal(actual, expected);
	});
});

test("CME helpers and validation helpers return expected results", async (t: TestContext) => {
	await t.test("1) generateCMEReport contains 3 rows and one complete status", () => {
		const report = generateCMEReport(sampleClinicians, "2025-03-20");
		const actual = { count: report.length, thirdStatus: report[2].complianceStatus };
		const expected = { count: 3, thirdStatus: "complete" };
		stepLog("generateCMEReport(sampleClinicians, 2025-03-20)", actual, expected);
		assert.equal(report.length, 3);
		assert.equal(report[2].complianceStatus, "complete");
	});

	await t.test("2) getCliniciansAtRisk returns none", () => {
		const actual = getCliniciansAtRisk(sampleClinicians, "2025-03-20");
		const expected: Clinician[] = [];
		stepLog("getCliniciansAtRisk(sampleClinicians, 2025-03-20)", actual, expected);
		assert.deepEqual(actual, expected);
	});

	await t.test("3) getCliniciansWithExpiringLicences returns CLN-000002", () => {
		const actual = getCliniciansWithExpiringLicences(sampleClinicians, "2025-03-20", 90).map(
			(clinician) => clinician.clinicianId
		);
		const expected = ["CLN-000002"];
		stepLog("getCliniciansWithExpiringLicences(..., 90)", actual, expected);
		assert.deepEqual(actual, expected);
	});

	await t.test("4) validateClaim returns valid result for known-good claim", () => {
		const knownLocationIds = sampleLocations.map((location) => location.locationId);
		const actual = validateClaim(sampleClaims[0], knownLocationIds);
		const expected = { valid: true, errors: [] };
		stepLog("validateClaim(sampleClaims[0])", actual, expected);
		assert.deepEqual(actual, expected);
	});

	await t.test("5) validateClaim returns errors for malformed denied claim", () => {
		const knownLocationIds = sampleLocations.map((location) => location.locationId);
		const invalidClaim = { ...sampleClaims[1], denialReason: undefined, patientId: "BAD" };
		const actual = validateClaim(invalidClaim, knownLocationIds);
		stepLog("validateClaim(invalid denied claim)", actual, {
			valid: false,
			errorsContain: ["denialReason is required", "patientId must match"],
		});
		assert.equal(actual.valid, false);
		assert.ok(actual.errors.some((error) => error.includes("denialReason is required")));
		assert.ok(actual.errors.some((error) => error.includes("patientId must match")));
	});

	await t.test("6) validateClinician returns valid result for active clinician", () => {
		const validClinician: Clinician = {
			clinicianId: "CLN-999999",
			firstName: "Nina",
			lastName: "Cole",
			role: "nurse",
			locationId: "us-tx-001",
			licenceState: "TX",
			licenceExpiryDate: "2099-01-01",
			cmeHoursRequired: 20,
			cmeHoursLogged: 12,
			cmeYearStartDate: "2025-01-01",
		};
		const actual = validateClinician(validClinician);
		const expected = { valid: true, errors: [] };
		stepLog("validateClinician(validClinician)", actual, expected);
		assert.deepEqual(actual, expected);
	});

	await t.test("7) validateClinician returns expected errors for expired clinician", () => {
		const expiredClinician: Clinician = {
			clinicianId: "CLN-999999",
			firstName: "Nina",
			lastName: "Cole",
			role: "nurse",
			locationId: "us-tx-001",
			licenceState: "TX",
			licenceExpiryDate: "2020-01-01",
			cmeHoursRequired: 20,
			cmeHoursLogged: -1,
			cmeYearStartDate: "2025-01-01",
		};
		const actual = validateClinician(expiredClinician);
		stepLog("validateClinician(expiredClinician)", actual, {
			valid: false,
			errorsContain: [
				"cmeHoursLogged must be greater than or equal to 0",
				"licenceExpiryDate is in the past",
			],
		});
		assert.equal(actual.valid, false);
		assert.ok(
			actual.errors.some((error) =>
				error.includes("cmeHoursLogged must be greater than or equal to 0")
			)
		);
		assert.ok(actual.errors.some((error) => error.includes("licenceExpiryDate is in the past")));
	});
});

test("calculateDenialRate throws on empty array", async (t: TestContext) => {
	await t.test("1) empty claims throws with expected message", () => {
		const expectedPattern = /Claims array cannot be empty/;
		console.log("[STEP] calculateDenialRate([]) should throw", expectedPattern.toString());
		assert.throws(() => calculateDenialRate([]), expectedPattern);
	});
});
