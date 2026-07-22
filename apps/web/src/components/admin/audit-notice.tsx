interface AuditNoticeProps {
  actionLabel: string;
}

/**
 * Visible copy that every mutating admin action writes an audit_logs row.
 * Required by Section 8 — no silent admin mutations.
 */
export function AuditNotice({ actionLabel }: AuditNoticeProps) {
  return (
    <p
      className="rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-200"
      role="note"
    >
      This action writes an <code className="font-mono text-amber-100">audit_logs</code>{" "}
      row for <span className="font-medium">{actionLabel}</span>. The backend must
      persist the audit entry alongside the mutation — never mute this step.
    </p>
  );
}
