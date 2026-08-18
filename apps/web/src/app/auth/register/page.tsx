"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  apiFetch,
  ApiError,
  setAccessToken,
} from "@/components/buyer/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface RegisterResponse {
  access_token?: string;
  accessToken?: string;
}

export default function RegisterPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");
    const fullName = String(form.get("name") ?? "").trim();
    const role = String(form.get("role") ?? "buyer");
    try {
      const body = await apiFetch<RegisterResponse>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
          role: role === "seller" ? "seller" : "buyer",
        }),
      });
      const token = body.access_token ?? body.accessToken;
      if (!token) {
        setError("Register succeeded but no access token was returned.");
        return;
      }
      setAccessToken(token);
      router.push("/map");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Registration failed.");
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
            Create your account
          </h1>
          <p className="mt-1 text-sm text-zinc-600">
            Start as a buyer. Sellers can list spaces after signup.
          </p>
        </div>

        <form
          className="space-y-4 rounded-xl border border-zinc-200 bg-white p-6 shadow-sm"
          onSubmit={(e) => void onSubmit(e)}
        >
          <input type="hidden" name="role" value="buyer" />
          <div className="space-y-2">
            <Label htmlFor="name">Full name</Label>
            <Input
              id="name"
              name="name"
              type="text"
              autoComplete="name"
              placeholder="Alex Morgan"
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
              placeholder="you@brand.com"
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
            {submitting ? "Signing up…" : "Sign up as a buyer"}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-zinc-600">
          Listing a space?{" "}
          <Link
            href="/auth/register/seller"
            className="font-medium text-[var(--brand-blue)] underline-offset-4 hover:underline"
          >
            Register as a seller
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
