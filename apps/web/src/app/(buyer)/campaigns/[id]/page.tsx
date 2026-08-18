import { CampaignDetailClient } from "@/components/buyer/campaign-detail-client";

export const metadata = {
  title: "Campaign · MarketPlays",
};

interface CampaignDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function CampaignDetailPage({
  params,
}: CampaignDetailPageProps) {
  const { id } = await params;
  return <CampaignDetailClient id={id} />;
}
