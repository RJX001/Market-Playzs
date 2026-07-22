import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

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

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <p className="text-xs text-muted-foreground">Campaign</p>
      <h1 className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
        {id}
      </h1>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Campaign detail stub</CardTitle>
          <CardDescription>
            Full timeline, deliverables, and review actions will connect here
            once bookings are live.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Link
            href="/campaigns"
            className={cn(buttonVariants({ variant: "outline" }))}
          >
            Back to campaigns
          </Link>
          <Link href="/map" className={cn(buttonVariants())}>
            Explore map
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
