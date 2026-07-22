import { BuyerShell } from "@/components/buyer/buyer-shell";

export default function BuyerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <BuyerShell>{children}</BuyerShell>;
}
