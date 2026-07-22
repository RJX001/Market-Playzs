import Link from "next/link";
import {
  sellerCardClass,
  sellerOutlineBtnClass,
  sellerPrimaryBtnClass,
} from "@/components/seller/seller-styles";

/** Quick actions stack — optional seller sidebar utility. */
export function QuickActions() {
  const actions = [
    { href: "/listings/new", label: "Create listing", primary: true },
    { href: "/bookings", label: "Review bookings", primary: false },
    { href: "/listings", label: "Manage listings", primary: false },
  ] as const;

  return (
    <section className={`${sellerCardClass} p-5`}>
      <h2 className="text-[16px] font-bold text-[#F5F6F8]">Quick actions</h2>
      <div className="mt-3 flex flex-col gap-2">
        {actions.map((action) => (
          <Link
            key={action.href}
            href={action.href}
            className={
              action.primary
                ? `${sellerPrimaryBtnClass} justify-start`
                : `${sellerOutlineBtnClass} justify-start`
            }
          >
            {action.label}
          </Link>
        ))}
      </div>
    </section>
  );
}
