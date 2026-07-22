"use client";

import { useEffect } from "react";
import { PortalHeader } from "@/components/shared/PortalHeader";
import { SELLER_NAV } from "@/lib/constants";

/**
 * Seller portal shell — dark app chrome (Section 4).
 * Home entry is Revenue Dashboard at /dashboard.
 */
export function SellerShell({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const root = document.documentElement;
    const hadDark = root.classList.contains("dark");
    root.classList.add("dark");
    return () => {
      if (!hadDark) root.classList.remove("dark");
    };
  }, []);

  return (
    <div className="dark min-h-screen bg-[#05070C] text-[#F5F6F8]">
      <PortalHeader
        role="seller"
        brandHref="/dashboard"
        navItems={[...SELLER_NAV]}
      />
      <main className="mx-auto max-w-[1200px] px-4 py-8 sm:px-7">{children}</main>
    </div>
  );
}
