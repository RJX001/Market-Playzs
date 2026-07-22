import { UsersTable } from "@/components/admin/users-table";
import { STUB_USERS } from "@/components/admin/stub-data";

export default function AdminUsersPage() {
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

      <UsersTable users={STUB_USERS} />
    </div>
  );
}
