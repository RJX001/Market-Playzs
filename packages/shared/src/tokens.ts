/**
 * Brand + map pin colour tokens (visual redesign Section 2.1 / 2.4).
 * App primary and landing accent differ by surface.
 */
export const APP_PRIMARY = "#3B5BFF" as const;
export const LANDING_ACCENT = "#2A47E8" as const;

/** @deprecated Prefer APP_PRIMARY in app chrome; LANDING_ACCENT on marketing. */
export const BRAND_BLUE = APP_PRIMARY;

export const PinColour = {
  available: "#22C55E",
  limited: "#F5A623",
  booked: "#F1544B",
  selected: "#3B5BFF",
  /** No-data / CIS-new listings — neutral grey (Section 2.2) */
  new: "#9AA3B2",
} as const;

export type PinColourKey = keyof typeof PinColour;
export type PinColour = (typeof PinColour)[PinColourKey];

export const PIN_COLOUR_CSS_VARS = {
  available: "--pin-available",
  limited: "--pin-limited",
  booked: "--pin-booked",
  selected: "--pin-selected",
  new: "--pin-new",
} as const;

/** Semantic status colours (Section 2.2). */
export const StatusColour = {
  green: { text: "#34D399", background: "#0C2A1D", border: "#155336" },
  amber: { text: "#F5A623", background: "#2E2409", border: "#5C4013" },
  red: { text: "#F1544B", background: "#301414", border: "#5C1F1F" },
  blue: { text: "#7AA2FF", background: "#101B33", border: "#233A6B" },
  neutral: { text: "#9AA3B2", background: "#171C26", border: "#262C38" },
} as const;
