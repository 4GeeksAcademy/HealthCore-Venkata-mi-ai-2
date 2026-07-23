import {
  calculateDenialRate,
  calculateNoShowCost,
  denialRateByPayer,
  flagHighDenialPayers,
  flagHighNoShowLocations,
  generateCMEReport,
  getCliniciansAtRisk,
  noShowRateByLocation,
} from "@hc/utils/transformations";
import {
  OPS_AS_OF_DATE,
  OPS_WEEK_ENDING,
  sampleAppointments,
  sampleClaims,
  sampleClinicians,
  sampleLocations,
} from "@/lib/sample-ops-data";

export interface Milestone2OpsSnapshot {
  denialRatePercent: number;
  denialRateByPayer: Record<string, number>;
  highDenialPayers: string[];
  noShowRateByLocation: Record<string, number>;
  highNoShowLocations: string[];
  miamiNoShowCostUsd: number;
  cliniciansAtRiskCount: number;
  cliniciansAtRiskIds: string[];
  cmeStatuses: Array<{
    clinicianId: string;
    fullName: string;
    complianceStatus: string;
    percentComplete: number;
  }>;
  asOfDate: string;
  weekEndingDate: string;
  source: string;
}

export function buildMilestone2OpsSnapshot(): Milestone2OpsSnapshot {
  const miami = sampleLocations[1];
  const cmeReport = generateCMEReport(sampleClinicians, OPS_AS_OF_DATE);
  const atRisk = getCliniciansAtRisk(sampleClinicians, OPS_AS_OF_DATE);

  return {
    denialRatePercent: calculateDenialRate(sampleClaims),
    denialRateByPayer: denialRateByPayer(sampleClaims),
    highDenialPayers: flagHighDenialPayers(sampleClaims),
    noShowRateByLocation: noShowRateByLocation(sampleAppointments),
    highNoShowLocations: flagHighNoShowLocations(sampleAppointments),
    miamiNoShowCostUsd: calculateNoShowCost(
      sampleAppointments,
      miami,
      OPS_WEEK_ENDING,
    ),
    cliniciansAtRiskCount: atRisk.length,
    cliniciansAtRiskIds: atRisk.map((clinician) => clinician.clinicianId),
    cmeStatuses: cmeReport.map((row) => ({
      clinicianId: row.clinicianId,
      fullName: row.fullName,
      complianceStatus: row.complianceStatus,
      percentComplete: row.percentComplete,
    })),
    asOfDate: OPS_AS_OF_DATE,
    weekEndingDate: OPS_WEEK_ENDING,
    source: "Milestone 2 src/utils (transformations) + synthetic sample data",
  };
}
