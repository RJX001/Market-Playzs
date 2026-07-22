"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const ADMIN_SUBNAV = [
  { href: "/admin", label: "Overview", exact: true },
  { href: "/admin/disputes", label: "Disputes", exact: false },
  { href: "/admin/users", label: "Users", exact: false },
  { href: "/admin/listings", label: "Listings", exact: false },
] as const;

function isActive(pathname: string, href: string, exact: boolean): boolean {
  if (exact) return pathname === href;
  return pathname === href || pathname.startsWith(`${href}/`);
}

/**
 * Secondary admin section links under the shared PortalHeader (Section 4 top bar
 * only shows "Admin"; these are in-panel section tabs).
 */
export function AdminSubnav({ className }: { className?: string }) {
  const pathname = usePathname();

  return (
    <nav
      className={cn(
        "flex flex-wrap gap-1 border-b border-[#1D2330] bg-[#0A0E16] px-7 py-2",
        className,
      )}
      aria-label="Admin sections"
    >
      {ADMIN_SUBNAV.map((item) => {
        const active = isActive(pathname, item.href, item.exact);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "rounded-[8px] px-3 py-1.5 text-[13px] font-medium transition-colors",
              active
                ? "bg-[#3B5BFF] text-white"
                : "text-[#9AA3B2] hover:bg-[#10141C] hover:text-[#F5F6F8]",
            )}
            aria-current={active ? "page" : undefined}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
