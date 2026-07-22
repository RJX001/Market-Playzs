import { penceToPoundsDisplay } from "@marketplays/shared";

/** Cards always show £/week = price_per_day × 7 (Section 6). */
export function formatWeeklyPriceFromDailyPence(pricePerDayPence: number): string {
  return `${penceToPoundsDisplay(pricePerDayPence * 7)}/week`;
}

export function weeklyPoundsFromDailyPence(pricePerDayPence: number): number {
  return (pricePerDayPence * 7) / 100;
}
