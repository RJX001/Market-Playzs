import Link from "next/link";
import { cn } from "@/lib/utils";

export type HeroCta = {
  label: string;
  href: string;
};

export type HeroSplitProps = {
  brandName?: string;
  headline: string;
  supporting: string;
  /** Exactly three verb + outcome bullets (Section 3). */
  bullets: readonly [string, string, string];
  primaryCta: HeroCta;
  secondaryCta: HeroCta;
  className?: string;
};

/**
 * Marketing hero — brand-first wordmark, H1, bullets, dual CTAs (Section 3).
 */
export function HeroSplit({
  brandName = "MarketPlays",
  headline,
  supporting,
  bullets,
  primaryCta,
  secondaryCta,
  className,
}: HeroSplitProps) {
  return (
    <section className={cn("relative isolate text-[#12141C]", className)}>
      <div className="mx-auto max-w-[1280px] px-6 pb-16 pt-6 sm:px-10 md:px-12 md:pb-20 md:pt-10">
        <div className="max-w-[720px]">
          <p
            className="font-[family-name:var(--font-lora),ui-serif,Georgia,serif] text-[40px] font-bold leading-[1.05] tracking-tight text-[#2A47E8] motion-safe:animate-[mp-fade-up_0.7s_ease-out_both] sm:text-[56px] md:text-[64px]"
          >
            {brandName}
          </p>

          <h1 className="mt-5 font-[family-name:var(--font-lora),ui-serif,Georgia,serif] text-[32px] font-bold leading-[1.15] tracking-tight text-[#12141C] motion-safe:animate-[mp-fade-up_0.7s_ease-out_0.1s_both] sm:text-[36px] md:text-[40px]">
            {headline}
          </h1>

          <p className="mt-4 max-w-xl font-[family-name:var(--font-inter),ui-sans-serif,system-ui,sans-serif] text-lg leading-relaxed text-[#5B6272] motion-safe:animate-[mp-fade-up_0.7s_ease-out_0.18s_both]">
            {supporting}
          </p>

          <ul className="mt-8 space-y-3 motion-safe:animate-[mp-fade-up_0.7s_ease-out_0.26s_both]">
            {bullets.map((bullet) => (
              <li
                key={bullet}
                className="flex items-start gap-3 font-[family-name:var(--font-inter),ui-sans-serif,system-ui,sans-serif] text-base text-[#363B47]"
              >
                <span
                  aria-hidden
                  className="mt-2 size-[6px] shrink-0 rounded-full bg-[#2A47E8]"
                />
                <span>{bullet}</span>
              </li>
            ))}
          </ul>

          <div className="mt-10 flex flex-col gap-3 motion-safe:animate-[mp-fade-up_0.7s_ease-out_0.34s_both] sm:flex-row sm:items-center">
            <Link
              href={primaryCta.href}
              className="inline-flex items-center justify-center rounded-[10px] bg-[#2A47E8] px-[26px] py-[15px] font-[family-name:var(--font-inter),ui-sans-serif,system-ui,sans-serif] text-base font-semibold text-white transition-colors hover:bg-[#2A47E8]/90"
            >
              {primaryCta.label}
            </Link>
            <Link
              href={secondaryCta.href}
              className="inline-flex items-center justify-center rounded-[10px] border border-[#C7D0EF] bg-white px-[26px] py-[15px] font-[family-name:var(--font-inter),ui-sans-serif,system-ui,sans-serif] text-base font-semibold text-[#2A47E8] transition-colors hover:bg-[#EEF1FB]"
            >
              {secondaryCta.label}
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
