"use client";

import { useEffect, useState } from "react";
import { UsersTable } from "@/components/admin/users-table";
import { getAdminUsers } from "@/components/admin/admin-api";
import { STUB_USERS, type AdminUser } from "@/components/admin/stub-data";

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>(STUB_USERS);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const items = await getAdminUsers();
        if (!cancelled && items) setUsers(items);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not load users.");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[26px] font-bold tracking-tight text-[#F5F6F8]">
          Users
        </h1>
        <p className="mt-1 text-[13px] text-[#9AA3B2]">
          Suspend accounts only with an audit trail — every suspend writes an{" "}
          <code className="font-mono text-[#C7CCD6]">audit_logs</code> row.
        </p>
      </div>

      {error ? (
        <p className="text-[13px] text-[#F1544B]" role="alert">
          {error}
        </p>
      ) : null}

      <UsersTable users={users} />
    </div>
  );
}
