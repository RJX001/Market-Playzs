import Link from "next/link";
import { cn } from "@/lib/utils";

export type MarketingHeaderProps = {
  className?: string;
};

/** Light marketing chrome only — no portal/dashboard nav. */
export function MarketingHeader({ className }: MarketingHeaderProps) {
  return (
    <header className={cn("relative z-20", className)}>
      <div className="mx-auto flex max-w-[1280px] items-center justify-between px-6 py-7 sm:px-10 md:px-12">
        <Link
          href="/"
          className="font-[family-name:var(--font-lora),ui-serif,Georgia,serif] text-[22px] font-bold leading-none tracking-tight text-[#2A47E8]"
        >
          MarketPlays
        </Link>
        <nav className="flex items-center gap-5">
          <Link
            href="/auth/login"
            className="font-[family-name:var(--font-inter),ui-sans-serif,system-ui,sans-serif] text-[15px] text-[#454C5C] transition-colors hover:text-[#12141C]"
          >
            Log in
          </Link>
          <Link
            href="/auth/register"
            className="rounded-[10px] bg-[#2A47E8] px-[22px] py-[11px] font-[family-name:var(--font-inter),ui-sans-serif,system-ui,sans-serif] text-[15px] font-semibold text-white transition-colors hover:bg-[#2A47E8]/90"
          >
            Sign up
          </Link>
        </nav>
      </div>
    </header>
  );
}
