"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/lib/constants";

export type PortalRole = "buyer" | "seller" | "admin";

export interface RoleToggleProps {
  /** Active portal role — prefer layout-provided role over path heuristics. */
  activeRole: PortalRole;
  className?: string;
}

const ROLE_HREF: Record<PortalRole, string> = {
  buyer: ROUTES.buyerMap,
  seller: ROUTES.sellerDashboard,
  admin: ROUTES.admin,
};

/**
 * Buyer / Seller / Admin segmented switcher (Section 4).
 * Active pill uses app primary #3B5BFF; switching resets to that role's home.
 */
export function RoleToggle({ activeRole, className }: RoleToggleProps) {
  return (
    <div
      className={cn(
        "inline-flex rounded-[9px] border border-[#262C38] bg-[#10141C] p-0.5 text-[12px] font-medium",
        className,
      )}
      role="group"
      aria-label="Switch portal role"
    >
      {(
        [
          { role: "buyer", label: "Buyer" },
          { role: "seller", label: "Seller" },
          { role: "admin", label: "Admin" },
        ] as const
      ).map(({ role, label }) => {
        const active = activeRole === role;
        return (
          <Link
            key={role}
            href={ROLE_HREF[role]}
            className={cn(
              "rounded-[7px] px-2.5 py-1.5 transition-colors",
              active
                ? "bg-[#3B5BFF] text-white"
                : "text-[#9AA3B2] hover:text-[#F5F6F8]",
            )}
            aria-current={active ? "page" : undefined}
          >
            {label}
          </Link>
        );
      })}
    </div>
  );
}
