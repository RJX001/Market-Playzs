import type { Metadata } from "next";
import { PortalHeader } from "@/components/shared/PortalHeader";
import { BUYER_NAV } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Messages · MarketPlays",
  description: "Buyer and seller message threads",
};

/**
 * Shared /messages route — usable from buyer or seller shell nav.
 * Default chrome role is buyer; RoleToggle still switches portals.
 */
export default function MessagesLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="dark min-h-screen bg-background text-foreground">
      <PortalHeader role="buyer" brandHref="/map" navItems={[...BUYER_NAV]} />
      <main>{children}</main>
    </div>
  );
}
