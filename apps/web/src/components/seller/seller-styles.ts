/** Seller portal visual tokens (redesign Sections 2, 8–11). */
export const SELLER = {
  card: "#10141C",
  border: "#262C38",
  borderSubtle: "#1D2330",
  input: "#171C26",
  primary: "#3B5BFF",
  text: "#F5F6F8",
  textSecondary: "#9AA3B2",
  textTertiary: "#6B7280",
  success: "#34D399",
  pageMax: "1200px",
} as const;

export const sellerCardClass =
  "rounded-[14px] border border-[#262C38] bg-[#10141C] text-[#F5F6F8] shadow-none ring-0";

export const sellerInputClass =
  "mt-1.5 w-full rounded-[9px] border border-[#262C38] bg-[#171C26] px-3 py-2.5 text-sm text-[#F5F6F8] placeholder:text-[#6B7280] outline-none focus-visible:border-[#3B5BFF] focus-visible:ring-2 focus-visible:ring-[#3B5BFF]/30";

export const sellerLabelClass =
  "block text-[12.5px] font-semibold uppercase tracking-[0.04em] text-[#9AA3B2]";

export const sellerPrimaryBtnClass =
  "inline-flex h-10 items-center justify-center rounded-[9px] bg-[#3B5BFF] px-4 text-sm font-semibold text-white transition-colors hover:bg-[#3B5BFF]/90 disabled:pointer-events-none disabled:opacity-50";

export const sellerOutlineBtnClass =
  "inline-flex h-10 items-center justify-center rounded-[9px] border border-[#262C38] bg-transparent px-4 text-sm font-medium text-[#F5F6F8] transition-colors hover:bg-[#171C26] disabled:pointer-events-none disabled:opacity-50";
