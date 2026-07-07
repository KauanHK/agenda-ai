import * as React from "react";
import { Icons } from "@/components/icons";
import { Button, EmptyState, FAB, Input, PageHeader, StatusBadge } from "@/components/ui";
import { useEstablishmentId } from "@/store/auth";
import { useToast } from "@/components/ToastProvider";
import * as schedulingsApi from "@/api/schedulings";
import { fmtDate, fmtDateLong, fmtTime } from "@/lib/date";
import type { SchedulingRead, SchedulingStatus, UUID } from "@/api/types";

const FILTERS = [
  { id: "upcoming", label: "Próximos" },
  { id: "pending", label: "Pendentes" },
  { id: "confirmed", label: "Confirmados" },
  { id: "completed", label: "Concluídos" },
  { id: "cancelled", label: "Cancelados" },
  { id: "past", label: "Histórico" },
] as const;

type FilterId = typeof FILTERS[number]["id"];

export const AppointmentsList: React.FC<{
  onCreate: () => void;
  onOpenAppointment: (id: string) => void;
  refreshKey?: number;
}> = ({ onCreate, onOpenAppointment, refreshKey }) => {
  const eid = useEstablishmentId();
  const toast = useToast();

  const [items, setItems] = React.useState<SchedulingRead[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [filter, setFilter] = React.useState<FilterId>("upcoming");
  const [search, setSearch] = React.useState("");


  const load = React.useCallback(async (f: FilterId) => {
    setLoading(true);
    try {
      const today = new Date(); today.setHours(0, 0, 0, 0);
      const todayIso = today.toISOString();
      const q: { status?: SchedulingStatus; starts_at_from?: string; starts_at_to?: string; size: number } = { size: 100 };

      if (f === "upcoming") q.starts_at_from = todayIso;
      else if (f === "past") q.starts_at_to = todayIso;
      else q.status = f as SchedulingStatus;

      const r = await schedulingsApi.listSchedulings(eid, q);
      setItems(r.data);
    } catch (e: any) {
      toast(e?.message ?? "Erro ao carregar agendamentos", "danger");
    } finally {
      setLoading(false);
    }
  }, [eid, toast]);

  React.useEffect(() => {
    load(filter);
  }, [filter, eid, refreshKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const displayed = items
    .filter((s) => {
      if (filter === "upcoming" && s.status === "cancelled") return false;
      if (!search) return true;
      return (
        s.client.name.toLowerCase().includes(search.toLowerCase()) ||
        s.client.phone.includes(search)
      );
    })
    .sort((a, b) =>
      filter === "past"
        ? +new Date(b.starts_at) - +new Date(a.starts_at)
        : +new Date(a.starts_at) - +new Date(b.starts_at)
    );

  const groups: Record<string, SchedulingRead[]> = {};
  displayed.forEach((s) => {
    const k = fmtDate(s.starts_at);
    (groups[k] = groups[k] || []).push(s);
  });

  return (
    <div className="page" style={{ padding: "var(--page-pad)" }}>
      <PageHeader
        title="Agenda"
        subtitle={loading ? "…" : `${displayed.length} resultado${displayed.length === 1 ? "" : "s"}`}
        action={<Button icon={<Icons.plus size={16} />} onClick={onCreate} className="hide-on-mobile">Novo</Button>}
      />

      <div style={{ marginBottom: 12 }}>
        <Input
          placeholder="Buscar por cliente…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          prefix={<Icons.search size={18} />}
        />
      </div>

      <div style={{ display: "flex", gap: 6, overflowX: "auto", marginBottom: 16, paddingBottom: 4, scrollbarWidth: "none" }}>
        {FILTERS.map((f) => (
          <button
            key={f.id}
            onClick={() => setFilter(f.id)}
            style={{
              flexShrink: 0, padding: "6px 14px", borderRadius: 999, fontSize: 13,
              cursor: "pointer", fontFamily: "inherit",
              background: filter === f.id ? "var(--text)" : "var(--surface)",
              color: filter === f.id ? "var(--bg)" : "var(--text)",
              border: `1px solid ${filter === f.id ? "var(--text)" : "var(--border)"}`,
              fontWeight: filter === f.id ? 500 : 400,
            }}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ padding: 32, textAlign: "center", color: "var(--text-dim)" }}>Carregando…</div>
      ) : displayed.length === 0 ? (
        <EmptyState
          icon={<Icons.list size={28} />}
          title="Nada por aqui"
          description="Tente outro filtro ou crie um novo agendamento."
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          {Object.entries(groups).map(([day, dayItems]) => (
            <div key={day}>
              <div style={{
                fontSize: 12, color: "var(--text-dim)", textTransform: "uppercase",
                letterSpacing: "0.06em", marginBottom: 8, fontWeight: 500,
              }}>
                {fmtDateLong(dayItems[0].starts_at)}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {dayItems.map((s) => {
                  return (
                    <button
                      key={s.id}
                      onClick={() => onOpenAppointment(s.id)}
                      style={{
                        display: "flex", alignItems: "center", gap: 14, width: "100%",
                        background: "var(--surface)", border: "1px solid var(--border)",
                        borderRadius: 14, padding: "12px 14px",
                        cursor: "pointer", textAlign: "left", fontFamily: "inherit",
                      }}
                    >
                      <div style={{
                        flexShrink: 0, width: 56, textAlign: "center",
                        borderRight: "1px solid var(--border)", paddingRight: 14,
                      }}>
                        <div style={{ fontFamily: "var(--font-display)", fontSize: 18, lineHeight: 1 }}>
                          {fmtTime(s.starts_at)}
                        </div>
                        <div style={{ fontSize: 11, color: "var(--text-dim)", marginTop: 2 }}>
                          {s.service.duration_minutes}min
                        </div>
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{
                          fontWeight: 500, fontSize: 15,
                          whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                        }}>
                          {s.client.name}
                        </div>
                        <div style={{
                          fontSize: 13, color: "var(--text-dim)", marginTop: 2,
                          whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                        }}>
                          {s.service.name} · {s.user.name.split(" ")[0]}
                        </div>
                      </div>
                      <StatusBadge status={s.status} />
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{ height: 80 }} />
      <FAB onClick={onCreate} />
    </div>
  );
};
