"use client";

import { useEffect, useRef, useState } from "react";
import type { Stripe, StripeElements } from "@stripe/stripe-js";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function StripePaymentForm({
  clientSecret,
  onPaid,
  onError,
}: {
  clientSecret: string;
  onPaid: () => void;
  onError: (message: string) => void;
}) {
  const mountRef = useRef<HTMLDivElement>(null);
  const stripeRef = useRef<Stripe | null>(null);
  const elementsRef = useRef<StripeElements | null>(null);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const key = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;
    if (!key) {
      onError("Card payments are not configured (missing publishable key).");
      return;
    }
    const node = mountRef.current;
    if (!node) return;
    let cancelled = false;
    void (async () => {
      const { loadStripe } = await import("@stripe/stripe-js");
      const stripe = await loadStripe(key);
      if (!stripe || cancelled) return;
      const elements = stripe.elements({
        clientSecret,
        appearance: { theme: "night" },
      });
      const paymentElement = elements.create("payment");
      paymentElement.mount(node);
      stripeRef.current = stripe;
      elementsRef.current = elements;
      setReady(true);
    })();
    return () => {
      cancelled = true;
    };
    // onError is a render callback; do not re-mount the Payment Element when it changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clientSecret]);

  async function pay(): Promise<void> {
    const stripe = stripeRef.current;
    const elements = elementsRef.current;
    if (!stripe || !elements) return;
    setBusy(true);
    try {
      const result = await stripe.confirmPayment({
        elements,
        confirmParams: { return_url: window.location.href },
        redirect: "if_required",
      });
      if (result.error) {
        onError(result.error.message ?? "Payment failed.");
        return;
      }
      onPaid();
    } catch {
      onError("Payment failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <div ref={mountRef} />
      <button
        type="button"
        disabled={!ready || busy}
        onClick={() => void pay()}
        className={cn(buttonVariants({ size: "lg" }), "w-full")}
      >
        {busy ? "Paying…" : "Pay now"}
      </button>
    </div>
  );
}

export function stripePublishableKey(): string | undefined {
  return process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;
}
