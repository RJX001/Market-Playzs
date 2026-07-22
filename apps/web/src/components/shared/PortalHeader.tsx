"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MarketPlaysLogo } from "@/components/shared/MarketPlaysLogo";
import { NotificationPanel } from "@/components/shared/NotificationPanel";
import {
  RoleToggle,
  type PortalRole,
} from "@/components/shared/RoleToggle";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";

export interface PortalNavItem {
  href: string;
  label: string;
}

export interface PortalHeaderProps {
  brandHref?: string;
  navItems: PortalNavItem[];
  /** Which portal this shell belongs to (drives role switcher active state). */
  role: PortalRole;
  className?: string;
}

/**
 * Shared sticky app shell top bar (Section 4).
 * 62px · #0A0E16 · logo + role nav · bell · role switcher · Exit.
 */
export function PortalHeader({
  brandHref,
  navItems,
  role,
  className,
}: PortalHeaderProps) {
  const pathname = usePathname();
  const homeHref =
    brandHref ??
    (role === "seller"
      ? ROUTES.sellerDashboard
      : role === "admin"
        ? ROUTES.admin
        : ROUTES.buyerMap);

  return (
    <header
      className={cn(
        "sticky top-0 z-40 h-[62px] border-b border-[#1D2330] bg-[#0A0E16]",
        className,
      )}
    >
      <div className="flex h-full items-center gap-5 px-7">
        <Link href={homeHref} className="shrink-0">
          <MarketPlaysLogo variant="app" />
        </Link>

        <nav
          className="flex min-w-0 flex-1 items-center gap-0.5 overflow-x-auto"
          aria-label="Portal"
        >
          {navItems.map((item) => {
            const active =
              pathname === item.href ||
              (item.href !== homeHref && pathname.startsWith(item.href));

            return (
              <Link
                key={`${item.href}-${item.label}`}
                href={item.href}
                className={cn(
                  "rounded-[8px] px-3 py-1.5 text-[13px] font-medium whitespace-nowrap transition-colors",
                  active
                    ? "bg-[#3B5BFF]/15 text-[#F5F6F8]"
                    : "text-[#9AA3B2] hover:bg-[#10141C] hover:text-[#F5F6F8]",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex shrink-0 items-center gap-2.5">
          <NotificationPanel />
          <RoleToggle activeRole={role} />
          <Link
            href={ROUTES.home}
            className="px-1 text-[13px] text-[#6B7280] transition-colors hover:text-[#9AA3B2]"
          >
            Exit
          </Link>
        </div>
      </div>
    </header>
  );
}
