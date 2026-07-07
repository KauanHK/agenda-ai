import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Icons } from "@/components/icons";
import { Button, Card, EmptyState, FAB, StatusBadge } from "@/components/ui";
import { useAuth } from "@/store/auth";
import { getDashboard } from "@/api/establishments";
import type { DashboardAgendaItem } from "@/api/types";
import { fmtDateLong, fmtTime } from "@/lib/date";

function todayISODate(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

const AgendaRow: React.FC<{ item: DashboardAgendaItem; onClick: () => void }> = ({ item, onClick }) => (
  <button onClick={onClick} style={{
    display: "flex", alignItems: "center", gap: 14, width: "100%",
    background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 14,
    padding: "12px 14px", cursor: "pointer", textAlign: "left", fontFamily: "inherit",
  }}>
    <div style={{ flexShrink: 0, width: 56, textAlign: "center", borderRight: "1px solid var(--border)", paddingRight: 14 }}>
      <div style={{ fontFamily: "var(--font-display)", fontSize: 18, lineHeight: 1 }}>{fmtTime(item.starts_at)}</div>
      <div style={{ fontSize: 11, color: "var(--text-dim)", marginTop: 2 }}>{item.service.duration_minutes}min</div>
    </div>
    <div style={{ flex: 1, minWidth: 0 }}>
      <div style={{ fontWeight: 500, fontSize: 15, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{item.client.name}</div>
      <div style={{ fontSize: 13, color: "var(--text-dim)", marginTop: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
        {item.service.name} · {item.user.name.split(" ")[0]}
      </div>
    </div>
    <StatusBadge status={item.status} />
  </button>
);

export const Dashboard: React.FC<{
  onCreate: () => void;
  onOpenAppointment: (id: string) => void;
}> = ({ onCreate, onOpenAppointment }) => {
  const navigate = useNavigate();
  const { user, activeEstablishment } = useAuth();
  const [data, setData] = React.useState<{
    today_total: number;
    today_confirmed: number;
    pending_count: number;
    expected_revenue: string;
    agenda: DashboardAgendaItem[];
  } | null>(null);
  const [loading, setLoading] = React.useState(true);

  const today = todayISODate();

  React.useEffect(() => {
    if (!activeEstablishment) return;
    setLoading(true);
    getDashboard(activeEstablishment.id, today)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [activeEstablishment, today]);

  const agenda = data?.agenda ?? [];
  const now = new Date();
  const nextUp = agenda.find((s) => s.status !== "cancelled" && new Date(s.starts_at) > now)
    ?? (agenda.length > 0 ? agenda[0] : null);

  const revenue = data ? parseFloat(data.expected_revenue) : 0;

  const Stat: React.FC<{ label: string; value: React.ReactNode; hint?: string; accent?: string }> = ({ label, value, hint, accent }) => (
    <Card style={{ flex: 1, minWidth: 0 }}>
      <div style={{ fontSize: 12, color: "var(--text-dim)", letterSpacing: "0.04em", textTransform: "uppercase" }}>{label}</div>
      <div style={{ fontFamily: "var(--font-display)", fontSize: 32, fontWeight: 400, marginTop: 4, lineHeight: 1, color: accent || "var(--text)" }}>{value}</div>
      {hint && <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 6 }}>{hint}</div>}
    </Card>
  );

  return (
    <div className="page" style={{ padding: "var(--page-pad)" }}>
      <div style={{ marginBottom: 22 }}>
        <div style={{ fontSize: 13, color: "var(--text-dim)", textTransform: "capitalize" }}>{fmtDateLong(new Date())}</div>
        <h1 style={{ margin: "4px 0 0", fontFamily: "var(--font-display)", fontSize: "var(--h1-size)", fontWeight: 400, letterSpacing: "-0.01em" }}>
          Olá, {user?.name.split(" ")[0] ?? "…"} 👋
        </h1>
        <div style={{ color: "var(--text-dim)", marginTop: 4, fontSize: 14 }}>
          {loading
            ? "Carregando…"
            : <>Você tem <strong style={{ color: "var(--text)" }}>{data?.today_total ?? 0} atendimentos</strong> hoje.</>}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 22 }}>
        <Stat label="Hoje" value={loading ? "—" : (data?.today_total ?? 0)} hint={loading ? undefined : `${data?.today_confirmed ?? 0} confirmados`} />
        <Stat label="Pendentes" value={loading ? "—" : (data?.pending_count ?? 0)} hint="aguardando" accent="var(--color-primary-deep)" />
        <Stat label="Faturamento" value={loading ? "—" : `R$${revenue.toFixed(0)}`} hint="previsto" />
      </div>

      {!loading && nextUp && (
        <Card style={{ marginBottom: 22, background: "linear-gradient(135deg, var(--color-primary), var(--color-primary-deep))", color: "white", border: 0 }}>
          <div style={{ fontSize: 12, opacity: 0.85, letterSpacing: "0.05em", textTransform: "uppercase" }}>Próximo</div>
          <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 12, marginTop: 6 }}>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontFamily: "var(--font-display)", fontSize: 28, lineHeight: 1.1 }}>{fmtTime(nextUp.starts_at)}</div>
              <div style={{ fontSize: 15, marginTop: 4, opacity: 0.95 }}>{nextUp.client.name}</div>
              <div style={{ fontSize: 13, opacity: 0.85, marginTop: 2 }}>
                {nextUp.service.name} · {nextUp.user.name.split(" ")[0]}
              </div>
            </div>
            <Button variant="secondary" size="sm" onClick={() => onOpenAppointment(nextUp.id)} style={{ background: "rgba(255,255,255,0.18)", border: "1px solid rgba(255,255,255,0.3)", color: "white" }}>
              Ver
            </Button>
          </div>
        </Card>
      )}

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <h2 style={{ margin: 0, fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 400 }}>Agenda do dia</h2>
        <button onClick={() => navigate("/calendar")} style={{ background: "transparent", border: 0, color: "var(--color-primary-deep)", fontSize: 13, fontWeight: 500, cursor: "pointer", fontFamily: "inherit" }}>
          Ver semana →
        </button>
      </div>

      {loading ? (
        <div style={{ color: "var(--text-dim)", fontSize: 14, textAlign: "center", padding: "32px 0" }}>Carregando…</div>
      ) : agenda.length === 0 ? (
        <EmptyState icon={<Icons.calendar size={28} />} title="Nenhum agendamento hoje"
          description="Aproveite para descansar ou criar um novo."
          action={<Button icon={<Icons.plus size={16} />} onClick={onCreate}>Novo agendamento</Button>} />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {agenda.map((item) => (
            <AgendaRow key={item.id} item={item} onClick={() => onOpenAppointment(item.id)} />
          ))}
        </div>
      )}

      <div style={{ height: 80 }} />
      <FAB onClick={onCreate} />
    </div>
  );
};
