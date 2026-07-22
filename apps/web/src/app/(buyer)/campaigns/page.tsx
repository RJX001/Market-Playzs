import { CampaignsPageClient } from "@/components/buyer/campaigns-page-client";

export const metadata = {
  title: "My campaigns & spend · MarketPlays",
  description:
    "Track everything you've booked across sellers, and where budget is going.",
};

export default function CampaignsPage() {
  return <CampaignsPageClient />;
}
