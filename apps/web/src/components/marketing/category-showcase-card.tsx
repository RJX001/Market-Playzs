import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import {
  Coffee,
  Dumbbell,
  GraduationCap,
  Landmark,
  Megaphone,
  PartyPopper,
  Store,
  Trophy,
  Users,
} from "lucide-react";
import { CATEGORY_LABELS, type Category } from "@marketplays/shared";
import { cn } from "@/lib/utils";

const CATEGORY_ICONS: Record<Category, LucideIcon> = {
  sports_club: Trophy,
  gym: Dumbbell,
  school: GraduationCap,
  shop: Store,
  cafe: Coffee,
  festival: PartyPopper,
  community_event: Users,
  billboard: Megaphone,
  event_venue: Landmark,
};

export type CategoryShowcaseCardProps = {
  category: Category;
  label?: string;
  href?: string;
  className?: string;
};

/**
 * Category grid tile — maps 1:1 to Category enum (Section 3).
 */
export function CategoryShowcaseCard({
  category,
  label,
  href = "/map",
  className,
}: CategoryShowcaseCardProps) {
  const Icon = CATEGORY_ICONS[category];
  const title = label ?? CATEGORY_LABELS[category];

  return (
    <Link
      href={href}
      className={cn(
        "group flex flex-col items-center gap-3 rounded-[14px] border border-[#E4E7F1] bg-white px-[18px] py-[26px] text-center transition-colors hover:border-[#C7D0EF] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2A47E8]/40",
        className,
      )}
    >
      <span className="flex size-[52px] items-center justify-center rounded-[12px] bg-[#EAF0FF] text-[#2A47E8]">
        <Icon className="size-6" strokeWidth={1.7} aria-hidden />
      </span>
      <span className="font-[family-name:var(--font-inter),ui-sans-serif,system-ui,sans-serif] text-[15px] font-semibold text-[#22252F]">
        {title}
      </span>
    </Link>
  );
}
