import * as React from "react";
import { Icons } from "@/components/icons";
import { StatusBadge } from "@/components/ui";
import { useStore } from "@/store/useStore";
import { fmtTime, fmtDateLong } from "@/lib/date";

export const AppointmentRow: React.FC<{
  schedulingId: string;
  onClick: () => void;
  showDate?: boolean;
}> = ({ schedulingId, onClick, showDate }) => {
  const item = useStore((s) => s.schedulings.find((x) => x.id === schedulingId));
  if (!item) return null;
  const { client, service, user } = item;

  return (
    <button onClick={onClick} style={{
      display: "flex", alignItems: "center", gap: 14, width: "100%",
      background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 14,
      padding: "12px 14px", cursor: "pointer", textAlign: "left", fontFamily: "inherit",
    }}>
      <div style={{ flexShrink: 0, width: 56, textAlign: "center", borderRight: "1px solid var(--border)", paddingRight: 14 }}>
        <div style={{ fontFamily: "var(--font-display)", fontSize: 18, lineHeight: 1 }}>{fmtTime(item.starts_at)}</div>
        <div style={{ fontSize: 11, color: "var(--text-dim)", marginTop: 2 }}>{service.duration_minutes}min</div>
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 500, fontSize: 15, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{client.name}</div>
        <div style={{ fontSize: 13, color: "var(--text-dim)", marginTop: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {service.name} · {user.name.split(" ")[0]}
          {showDate && <> · {fmtDateLong(item.starts_at)}</>}
        </div>
      </div>
      <StatusBadge status={item.status} />
    </button>
  );
};
