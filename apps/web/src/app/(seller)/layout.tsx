import type { Metadata } from "next";
import { SellerShell } from "@/components/seller/seller-shell";

export const metadata: Metadata = {
  title: "Seller · MarketPlays",
  description: "MarketPlays seller revenue dashboard and listings",
};

/**
 * Seller portal shell — always dark mode (Section 4).
 * Home entry is Revenue Dashboard at /dashboard.
 */
export default function SellerLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <SellerShell>{children}</SellerShell>;
}
