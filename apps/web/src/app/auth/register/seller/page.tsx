"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function apiUrl(path: string): string {
  const base = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");
  return `${base}${path}`;
}

async function readError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown; error?: string };
    const detail = body.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) =>
          typeof item === "string"
            ? item
            : String((item as { msg?: string }).msg ?? JSON.stringify(item)),
        )
        .join("; ");
    }
    return body.error ?? `Registration failed (${res.status})`;
  } catch {
    return `Registration failed (${res.status})`;
  }
}

export default function SellerRegisterPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    const form = new FormData(event.currentTarget);
    try {
      const res = await fetch(apiUrl("/api/auth/register"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          email: String(form.get("email") ?? ""),
          password: String(form.get("password") ?? ""),
          full_name: String(form.get("name") ?? ""),
          role: "seller",
          company_name: String(form.get("business") ?? "") || undefined,
        }),
      });
      if (!res.ok) {
        setError(await readError(res));
        return;
      }
      const data = (await res.json()) as {
        access_token?: string;
        user?: { id?: string; role?: string };
      };
      if (data.access_token) {
        localStorage.setItem("mp_access_token", data.access_token);
      }
      localStorage.setItem("mp_role", "seller");
      if (data.user?.id) {
        localStorage.setItem("mp_user_id", String(data.user.id));
      }
      router.push("/dashboard");
    } catch {
      setError("Could not register. Check the API is running.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-[100svh] items-center justify-center bg-[#F7F9FC] px-4 py-12 text-zinc-900">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <Link
            href="/"
            className="font-[family-name:var(--font-display)] text-2xl font-bold text-[var(--brand-blue)]"
          >
            MarketPlays
          </Link>
          <h1 className="mt-4 text-xl font-semibold tracking-tight">
            Seller registration
          </h1>
          <p className="mt-1 text-sm text-zinc-600">
            List your space and start earning from local campaigns.
          </p>
        </div>

        <form
          className="space-y-4 rounded-xl border border-zinc-200 bg-white p-6 shadow-sm"
          onSubmit={onSubmit}
        >
          <input type="hidden" name="role" value="seller" />
          <div className="space-y-2">
            <Label htmlFor="name">Full name</Label>
            <Input
              id="name"
              name="name"
              type="text"
              autoComplete="name"
              placeholder="Jordan Lee"
              required
              className="h-10"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="business">Business or venue name</Label>
            <Input
              id="business"
              name="business"
              type="text"
              autoComplete="organization"
              placeholder="Northside Sports Club"
              required
              className="h-10"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="you@venue.com"
              required
              className="h-10"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              className="h-10"
            />
          </div>
          {error ? (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          ) : null}
          <Button
            type="submit"
            disabled={submitting}
            className="h-10 w-full bg-[var(--brand-blue)] text-white hover:bg-[var(--brand-blue)]/90"
          >
            {submitting ? "Signing up…" : "Sign up as a seller"}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-zinc-600">
          Looking to book space?{" "}
          <Link
            href="/auth/register"
            className="font-medium text-[var(--brand-blue)] underline-offset-4 hover:underline"
          >
            Register as a buyer
          </Link>
        </p>
        <p className="mt-2 text-center text-sm text-zinc-600">
          Already have an account?{" "}
          <Link
            href="/auth/login"
            className="font-medium text-[var(--brand-blue)] underline-offset-4 hover:underline"
          >
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
