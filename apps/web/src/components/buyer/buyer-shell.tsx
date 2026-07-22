"use client";

import { useEffect } from "react";
import { PortalHeader } from "@/components/shared/PortalHeader";
import { BUYER_NAV } from "@/lib/constants";

/**
 * Forces dark mode for logged-in buyer chrome (Section 4).
 * Uses a `.dark` ancestor so Tailwind dark: tokens apply without fighting marketing light pages.
 */
export function BuyerShell({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const root = document.documentElement;
    const hadDark = root.classList.contains("dark");
    root.classList.add("dark");
    return () => {
      if (!hadDark) root.classList.remove("dark");
    };
  }, []);

  return (
    <div className="dark min-h-screen bg-background text-foreground">
      <PortalHeader
        role="buyer"
        brandHref="/map"
        navItems={[...BUYER_NAV]}
      />
      <main className="min-h-0 flex-1">{children}</main>
    </div>
  );
}
