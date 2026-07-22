"use client";

import { useEffect } from "react";
import { AdminSubnav } from "@/components/admin/admin-subnav";
import { PortalHeader } from "@/components/shared/PortalHeader";
import { ADMIN_NAV } from "@/lib/constants";

/**
 * Admin portal shell — dark app chrome (Section 4).
 * Top-bar nav is the single "Admin" tab; panel content lives under /admin/*.
 */
export function AdminShell({ children }: { children: React.ReactNode }) {
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
      <PortalHeader role="admin" brandHref="/admin" navItems={[...ADMIN_NAV]} />
      <AdminSubnav />
      <main className="mx-auto max-w-[1200px] px-7 py-8">{children}</main>
    </div>
  );
}
