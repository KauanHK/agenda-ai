import * as React from "react";
import { Icons } from "@/components/icons";
import { Button, Card, IconButton, FAB } from "@/components/ui";
import { useEstablishmentId } from "@/store/auth";
import { useToast } from "@/components/ToastProvider";
import * as schedulingsApi from "@/api/schedulings";
import * as membersApi from "@/api/members";
import { fmtTime, sameDay, getWeekday, WEEKDAYS, MONTHS } from "@/lib/date";
import type { SchedulingRead } from "@/api/types";

function memberColor(id: string) {
  let h = 0;
  for (const c of id) h = ((h << 5) - h) + c.charCodeAt(0) | 0;
  return `hsl(${Math.abs(h) % 360},55%,45%)`;
}

interface TeamMember { id: string; name: string; color: string; }

export const WeekCalendar: React.FC<{
  onCreate: (date?: Date, hour?: number | null) => void;
  onOpenAppointment: (id: string) => void;
  refreshKey?: number;
}> = ({ onCreate, onOpenAppointment, refreshKey }) => {
  const eid = useEstablishmentId();
  const toast = useToast();

  const [anchor, setAnchor] = React.useState(() => {
    const d = new Date(); d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() - getWeekday(d));
    return d;
  });
  const [filterUser, setFilterUser] = React.useState("all");
  const [schedulings, setSchedulings] = React.useState<SchedulingRead[]>([]);
  const [team, setTeam] = React.useState<TeamMember[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    membersApi.listMembers(eid, { size: 50 })
      .then((mr) => {
        const members: TeamMember[] = mr.data
          .filter((m) => m.user.is_active)
          .map((m) => ({ id: m.user.id, name: m.user.name, color: memberColor(m.user.id) }));
        setTeam(members);
      }).catch(() => {});
  }, [eid]);

  const days = React.useMemo(() => Array.from({ length: 7 }, (_, i) => {
    const d = new Date(anchor); d.setDate(anchor.getDate() + i); return d;
  }), [anchor]);

  React.useEffect(() => {
    const weekEnd = new Date(anchor);
    weekEnd.setDate(anchor.getDate() + 7);
    setLoading(true);
    schedulingsApi.listSchedulings(eid, {
      starts_at_from: anchor.toISOString(),
      starts_at_to: weekEnd.toISOString(),
      size: 100,
    })
      .then((r) => setSchedulings(r.data))
      .catch((e: any) => toast(e?.message ?? "Erro ao carregar agendamentos", "danger"))
      .finally(() => setLoading(false));
  }, [eid, anchor, refreshKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const HOURS = Array.from({ length: 12 }, (_, i) => i + 8);

  const filtered = schedulings.filter((s) =>
    (filterUser === "all" || s.user.id === filterUser) &&
    s.status !== "cancelled"
  );

  const monthLabel = `${MONTHS[anchor.getMonth()]} ${anchor.getFullYear()}`;
  const shiftWeek = (dir: number) => {
    const d = new Date(anchor); d.setDate(d.getDate() + dir * 7); setAnchor(d);
  };
  const goToday = () => {
    const d = new Date(); d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() - getWeekday(d)); setAnchor(d);
  };

  return (
    <div className="page" style={{ padding: "var(--page-pad)" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14, gap: 8, flexWrap: "wrap" }}>
        <div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 26, lineHeight: 1.1, textTransform: "capitalize" }}>{monthLabel}</div>
          <div style={{ fontSize: 12, color: "var(--text-dim)" }}>Semana de {String(anchor.getDate()).padStart(2, "0")}/{String(anchor.getMonth() + 1).padStart(2, "0")}</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {loading && <span style={{ fontSize: 12, color: "var(--text-dim)" }}>Carregando…</span>}
          <IconButton icon={<Icons.chevronLeft size={18} />} onClick={() => shiftWeek(-1)} />
          <Button variant="secondary" size="sm" onClick={goToday}>Hoje</Button>
          <IconButton icon={<Icons.chevronRight size={18} />} onClick={() => shiftWeek(1)} />
        </div>
      </div>

      <div style={{ marginBottom: 12, display: "flex", gap: 6, overflowX: "auto", paddingBottom: 4, scrollbarWidth: "none" }}>
        {[{ id: "all", name: "Todos", color: "" }, ...team].map((t) => (
          <button key={t.id} onClick={() => setFilterUser(t.id)} style={{
            display: "inline-flex", alignItems: "center", gap: 6, flexShrink: 0,
            padding: "6px 12px", borderRadius: 999, fontSize: 13, cursor: "pointer", fontFamily: "inherit",
            background: filterUser === t.id ? "var(--color-primary-soft)" : "var(--surface)",
            border: `1px solid ${filterUser === t.id ? "transparent" : "var(--border)"}`,
            color: filterUser === t.id ? "var(--color-primary-deep)" : "var(--text)",
            fontWeight: filterUser === t.id ? 600 : 400,
          }}>
            {t.id !== "all" && <span style={{ width: 8, height: 8, borderRadius: 999, background: t.color }} />}
            {t.name.split(" ")[0]}
          </button>
        ))}
      </div>

      <Card padded={false} style={{ overflow: "hidden" }}>
        <div style={{ overflowX: "auto" }}>
          <div style={{ minWidth: 720, display: "grid", gridTemplateColumns: "48px repeat(7, minmax(90px,1fr))" }}>
            <div style={{ borderBottom: "1px solid var(--border)", borderRight: "1px solid var(--border)" }} />
            {days.map((d, i) => {
              const isToday = sameDay(d, new Date());
              return (
                <div key={i} style={{
                  padding: "10px 8px", borderBottom: "1px solid var(--border)",
                  borderRight: i < 6 ? "1px solid var(--border)" : 0,
                  textAlign: "center",
                  background: isToday ? "var(--color-primary-soft)" : "transparent",
                }}>
                  <div style={{ fontSize: 11, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{WEEKDAYS[i]}</div>
                  <div style={{ fontFamily: "var(--font-display)", fontSize: 20, marginTop: 2, color: isToday ? "var(--color-primary-deep)" : "var(--text)" }}>{d.getDate()}</div>
                </div>
              );
            })}

            {HOURS.map((h) => (
              <React.Fragment key={h}>
                <div style={{
                  borderRight: "1px solid var(--border)", borderBottom: "1px solid var(--border)",
                  padding: "4px 6px", fontSize: 10, color: "var(--text-dim)", textAlign: "right",
                  height: 56, fontVariantNumeric: "tabular-nums",
                }}>{String(h).padStart(2, "0")}:00</div>
                {days.map((d, i) => {
                  const slotStart = new Date(d); slotStart.setHours(h, 0, 0, 0);
                  const slotEnd = new Date(d); slotEnd.setHours(h + 1, 0, 0, 0);
                  const items = filtered.filter((s) => {
                    const t = new Date(s.starts_at);
                    return sameDay(t, d) && t >= slotStart && t < slotEnd;
                  });
                  const isToday = sameDay(d, new Date());
                  return (
                    <div key={i} onClick={() => onCreate(d, h)} style={{
                      borderRight: i < 6 ? "1px solid var(--border)" : 0,
                      borderBottom: "1px solid var(--border)",
                      height: 56, position: "relative", cursor: "pointer",
                      background: isToday ? "rgba(201,123,92,0.04)" : "transparent",
                    }}>
                      {items.map((s, idx) => {
                        const member = team.find((u) => u.id === s.user.id);
                        const t = new Date(s.starts_at);
                        const offsetMin = t.getMinutes();
                        const heightPct = Math.min(((s.service.duration_minutes || 30) / 60) * 100, 100);
                        return (
                          <div key={s.id} onClick={(e) => { e.stopPropagation(); onOpenAppointment(s.id); }} style={{
                            position: "absolute",
                            top: `${(offsetMin / 60) * 100}%`,
                            left: items.length > 1 ? `${(idx / items.length) * 100}%` : 2,
                            width: items.length > 1 ? `${100 / items.length}%` : "calc(100% - 4px)",
                            height: `${heightPct}%`, minHeight: 22,
                            background: member?.color || "var(--color-primary)",
                            borderRadius: 6, padding: "3px 6px",
                            color: "white", fontSize: 11, lineHeight: 1.15, overflow: "hidden",
                            boxShadow: "0 1px 2px rgba(0,0,0,0.08)",
                            opacity: s.status === "pending" ? 0.7 : 1,
                            border: s.status === "pending" ? "1px dashed rgba(255,255,255,0.5)" : "none",
                          }}>
                            <div style={{ fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                              {fmtTime(s.starts_at)} {s.client.name.split(" ")[0]}
                            </div>
                            <div style={{ opacity: 0.85, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{s.service.name}</div>
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
              </React.Fragment>
            ))}
          </div>
        </div>
      </Card>

      <div style={{ height: 80 }} />
      <FAB onClick={() => onCreate(new Date(), null)} />
    </div>
  );
};
