import { HeroSplit } from "@/components/marketing/hero-split";
import { CategoryShowcaseStrip } from "@/components/marketing/category-showcase-strip";
import { MarketingHeader } from "@/components/marketing/marketing-header";

export default function MarketingHomePage() {
  return (
    <div
      className="min-h-[100svh] text-[#12141C]"
      style={{
        background:
          "linear-gradient(180deg, #EEF1FB 0%, #E2E8FB 55%, #FFFFFF 100%)",
      }}
    >
      <MarketingHeader />
      <HeroSplit
        brandName="MarketPlays"
        headline="Book local spaces that convert"
        supporting="Discover and reserve real-world advertising inventory — physical and digital — near the audiences you care about."
        bullets={[
          "Discover spaces near your audience",
          "Book campaigns in a few clicks, or bundle several into one order",
          "Track presence with proof-of-play and a live Community Impact Score",
        ]}
        primaryCta={{ label: "Browse as a buyer", href: "/map" }}
        secondaryCta={{
          label: "List as a seller",
          href: "/auth/register/seller",
        }}
      />
      <CategoryShowcaseStrip />
      <footer className="border-t border-[#E4E7F1] px-12 py-[26px]">
        <div className="mx-auto flex max-w-[1280px] flex-col items-center justify-between gap-3 text-[14px] text-[#8A90A0] sm:flex-row">
          <p>© {new Date().getFullYear()} MarketPlays</p>
          <p>Local advertising spaces, booked on a live map.</p>
        </div>
      </footer>
    </div>
  );
}
