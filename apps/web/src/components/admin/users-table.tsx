"use client";

import { useState, useTransition } from "react";
import { AuditNotice } from "@/components/admin/audit-notice";
import { suspendUser } from "@/components/admin/admin-api";
import type { AdminUser } from "@/components/admin/stub-data";

interface UsersTableProps {
  users: AdminUser[];
}

export function UsersTable({ users }: UsersTableProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const selected = users.find((u) => u.id === selectedId) ?? null;

  function handleSuspend() {
    if (!selected || !reason.trim()) {
      setMessage("Enter a suspension reason before continuing.");
      return;
    }

    startTransition(async () => {
      setMessage(null);
      // TODO: real /api/admin/users/{id}/suspend — server writes audit_logs
      const result = await suspendUser({
        userId: selected.id,
        reason: reason.trim(),
      });
      setMessage(
        result.stub
          ? `Stub OK: ${result.path} (audit_logs row will be written by API).`
          : "User suspended.",
      );
      setSelectedId(null);
      setReason("");
    });
  }

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto rounded-lg border border-zinc-800">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-zinc-800 bg-zinc-900 text-zinc-400">
            <tr>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Email</th>
              <th className="px-4 py-3 font-medium">Role</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Joined</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr
                key={user.id}
                className="border-b border-zinc-800/80 last:border-0"
              >
                <td className="px-4 py-3 text-zinc-100">{user.name}</td>
                <td className="px-4 py-3 text-zinc-300">{user.email}</td>
                <td className="px-4 py-3 capitalize text-zinc-300">{user.role}</td>
                <td className="px-4 py-3">
                  <span
                    className={
                      user.status === "suspended"
                        ? "text-red-400"
                        : "text-emerald-400"
                    }
                  >
                    {user.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-zinc-400">{user.createdAt}</td>
                <td className="px-4 py-3">
                  {user.status === "active" && user.role !== "admin" ? (
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedId(user.id);
                        setMessage(null);
                      }}
                      className="text-sm text-red-300 hover:text-red-200"
                    >
                      Suspend
                    </button>
                  ) : (
                    <span className="text-zinc-600">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected ? (
        <div className="space-y-3 rounded-lg border border-zinc-800 bg-zinc-900/60 p-4">
          <h2 className="text-sm font-semibold text-zinc-50">
            Suspend {selected.name}
          </h2>
          <label className="block text-sm text-zinc-300">
            Reason
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              className="mt-1 w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
              placeholder="Internal reason for audit trail"
            />
          </label>
          <AuditNotice actionLabel={`suspend user ${selected.email}`} />
          <div className="flex gap-2">
            <button
              type="button"
              disabled={isPending}
              onClick={handleSuspend}
              className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {isPending ? "Submitting…" : "Confirm suspend"}
            </button>
            <button
              type="button"
              onClick={() => {
                setSelectedId(null);
                setReason("");
              }}
              className="rounded-md border border-zinc-700 px-4 py-2 text-sm text-zinc-300"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : null}

      {message ? (
        <p className="text-xs text-emerald-400" role="status">
          {message}
        </p>
      ) : null}
    </div>
  );
}
