/**
 * Money helpers — DB stores integer pence; format £ only at the presentation layer.
 */

/** Convert integer pence to a GBP display string (e.g. 1250 → "£12.50"). */
export function penceToPoundsDisplay(pence: number): string {
  if (!Number.isInteger(pence)) {
    throw new Error("pence must be an integer");
  }
  const pounds = pence / 100;
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
  }).format(pounds);
}

/** Convert pounds (may be float from UI) to integer pence. */
export function poundsToPence(pounds: number): number {
  return Math.round(pounds * 100);
}
