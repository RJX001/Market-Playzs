/**
 * CIS (Community Impact Score) badge thresholds — visual redesign Section 2.3.
 * Code/variable names stay "CIS"; user-facing name is "Community Impact Score".
 * Colour always follows the band — never a fixed colour independent of score.
 * null score = "CIS New" (grey), not zero.
 *
 * Thresholds: ≥85 green · 60–84 amber · <60 red · null grey
 */
export const CisBand = {
  excellent: "excellent",
  good: "good",
  at_risk: "at_risk",
  new: "new",
} as const;

export type CisBand = (typeof CisBand)[keyof typeof CisBand];

export interface CisBandMeta {
  band: CisBand;
  /** Short band name for tooltips / accessibility */
  label: string;
  /** Inclusive min; null for New */
  min: number | null;
  /** Inclusive max; null for New */
  max: number | null;
  /** Text / accent (Section 2.2) */
  color: string;
  /** Badge background (Section 2.2) */
  background: string;
  /** Badge border (Section 2.2) */
  border: string;
}

export const CIS_BANDS: Record<CisBand, CisBandMeta> = {
  excellent: {
    band: "excellent",
    label: "Excellent",
    min: 85,
    max: 100,
    color: "#34D399",
    background: "#0C2A1D",
    border: "#155336",
  },
  good: {
    band: "good",
    label: "Good",
    min: 60,
    max: 84,
    color: "#F5A623",
    background: "#2E2409",
    border: "#5C4013",
  },
  at_risk: {
    band: "at_risk",
    label: "At risk",
    min: 0,
    max: 59,
    color: "#F1544B",
    background: "#301414",
    border: "#5C1F1F",
  },
  new: {
    band: "new",
    label: "New",
    min: null,
    max: null,
    color: "#9AA3B2",
    background: "#171C26",
    border: "#262C38",
  },
};

/** User-facing product name for CIS (Section 15). */
export const CIS_DISPLAY_NAME = "Community Impact Score" as const;

/** Resolve CIS score (nullable) to its band metadata. */
export function getCisBand(score: number | null | undefined): CisBandMeta {
  if (score === null || score === undefined) {
    return CIS_BANDS.new;
  }
  if (score >= 85) {
    return CIS_BANDS.excellent;
  }
  if (score >= 60) {
    return CIS_BANDS.good;
  }
  return CIS_BANDS.at_risk;
}

/** Badge label: "CIS New" or "CIS {score}". */
export function formatCisBadgeLabel(score: number | null | undefined): string {
  if (score === null || score === undefined) {
    return "CIS New";
  }
  return `CIS ${score}`;
}
