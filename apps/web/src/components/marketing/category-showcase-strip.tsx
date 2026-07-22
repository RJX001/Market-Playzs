import Link from "next/link";
import {
  CATEGORY_VALUES,
  type Category,
} from "@marketplays/shared";
import { CategoryShowcaseCard } from "@/components/marketing/category-showcase-card";
import { cn } from "@/lib/utils";

export type CategoryShowcaseStripProps = {
  hrefForCategory?: (category: Category) => string;
  className?: string;
};

/**
 * Category grid — all 9 enum values in a 5-column layout (Section 3).
 */
export function CategoryShowcaseStrip({
  hrefForCategory = () => "/map",
  className,
}: CategoryShowcaseStripProps) {
  return (
    <section
      className={cn("py-[70px]", className)}
      aria-labelledby="category-showcase-heading"
    >
      <div className="mx-auto max-w-[1280px] px-6 sm:px-10 md:px-12">
        <div className="max-w-2xl">
          <h2
            id="category-showcase-heading"
            className="font-[family-name:var(--font-lora),ui-serif,Georgia,serif] text-[28px] font-bold tracking-tight text-[#12141C] sm:text-[32px]"
          >
            Spaces across every local format
          </h2>
          <p className="mt-2 font-[family-name:var(--font-inter),ui-sans-serif,system-ui,sans-serif] text-base text-[#6B7280]">
            Browse advertising inventory mapped to the places people already
            gather.
          </p>
        </div>

        <div className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 lg:gap-4">
          {CATEGORY_VALUES.map((category) => (
            <CategoryShowcaseCard
              key={category}
              category={category}
              href={hrefForCategory(category)}
            />
          ))}
        </div>

        <p className="mt-8 text-center font-[family-name:var(--font-inter),ui-sans-serif,system-ui,sans-serif] text-base text-[#6B7280]">
          Ready to book?{" "}
          <Link
            href="/map"
            className="font-medium text-[#2A47E8] underline-offset-4 hover:underline"
          >
            Open the map
          </Link>
        </p>
      </div>
    </section>
  );
}
