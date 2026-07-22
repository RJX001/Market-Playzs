"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/admin", label: "Overview", exact: true },
  { href: "/admin/disputes", label: "Disputes", exact: false },
  { href: "/admin/users", label: "Users", exact: false },
  { href: "/admin/listings", label: "Listings", exact: false },
] as const;

function isActive(pathname: string, href: string, exact: boolean): boolean {
  if (exact) return pathname === href;
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AdminNav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-[#1D2330] bg-[#0A0E16]">
      <div className="mx-auto flex max-w-[1200px] flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-[11.5px] uppercase tracking-widest text-[#6B7280]">
            MarketPlays
          </p>
          <h1 className="text-[18px] font-semibold text-[#F5F6F8]">Admin</h1>
        </div>
        <nav className="flex flex-wrap gap-1" aria-label="Admin">
          {NAV_ITEMS.map((item) => {
            const active = isActive(pathname, item.href, item.exact);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={
                  active
                    ? "rounded-[9px] bg-[#3B5BFF] px-3 py-1.5 text-[13px] font-medium text-white"
                    : "rounded-[9px] px-3 py-1.5 text-[13px] text-[#9AA3B2] hover:bg-[#171C26] hover:text-[#F5F6F8]"
                }
                aria-current={active ? "page" : undefined}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
