import * as React from "react";
import { Icons } from "@/components/icons";
import { Avatar, Button, IconButton, Input, StatusBadge } from "@/components/ui";
import { useEstablishmentId } from "@/store/auth";
import { useToast } from "@/components/ToastProvider";
import * as schedulingsApi from "@/api/schedulings";
import { fmtDate, fmtDateLong, fmtTime } from "@/lib/date";
import type { CancelledByType, SchedulingExpandedRead, SchedulingStatusLogRead } from "@/api/types";

function memberColor(id: string) {
  let h = 0;
  for (const c of id) h = ((h << 5) - h) + c.charCodeAt(0) | 0;
  return `hsl(${Math.abs(h) % 360},55%,45%)`;
}

const LOG_LABELS: Record<string, string> = {
  pending: "Pendente", confirmed: "Confirmado", cancelled: "Cancelado", completed: "Concluído",
};
const LOG_SOURCE: Record<string, string> = {
  user: "Usuário", client: "Cliente", system: "Sistema",
};

const Row: React.FC<{ icon: React.ReactNode; label: string; value: React.ReactNode }> = ({ icon, label, value }) => (
  <div style={{ display: "flex", alignItems: "flex-start", gap: 12, padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
    <div style={{ color: "var(--color-primary)", marginTop: 1 }}>{icon}</div>
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: 11, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</div>
      <div style={{ fontSize: 14, marginTop: 2 }}>{value}</div>
    </div>
  </div>
);

export const AppointmentDetail: React.FC<{
  id: string;
  onEdit: (item: any) => void;
  onClose: () => void;
  onSuccess?: () => void;
}> = ({ id, onEdit, onClose: _onClose, onSuccess }) => {
  const eid = useEstablishmentId();
  const toast = useToast();

  const [item, setItem] = React.useState<SchedulingExpandedRead | null>(null);
  const [logs, setLogs] = React.useState<SchedulingStatusLogRead[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [acting, setActing] = React.useState(false);
  const [showReschedule, setShowReschedule] = React.useState(false);
  const [rescheduleDate, setRescheduleDate] = React.useState("");
  const [rescheduleHour, setRescheduleHour] = React.useState("");
  const [showCancel, setShowCancel] = React.useState(false);
  const [cancelledBy, setCancelledBy] = React.useState<CancelledByType>("establishment");

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const [s, l] = await Promise.all([
        schedulingsApi.getScheduling(eid, id),
        schedulingsApi.listSchedulingLogs(eid, id, { size: 20 }),
      ]);
      setItem(s);
      setLogs(l.data);
      const d = new Date(s.starts_at);
      setRescheduleDate(
        `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`
      );
      setRescheduleHour(
        `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`
      );
    } catch (e: any) {
      toast(e?.message ?? "Erro ao carregar agendamento", "danger");
    } finally {
      setLoading(false);
    }
  }, [eid, id, toast]);

  React.useEffect(() => { load(); }, [load]);

  const act = async (fn: () => Promise<void>) => {
    if (acting) return;
    setActing(true);
    try {
      await fn();
      await load();
      onSuccess?.();
    } catch (e: any) {
      toast(e?.message ?? "Erro ao executar ação", "danger");
    } finally {
      setActing(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: "40px 0", textAlign: "center", color: "var(--text-dim)", fontSize: 14 }}>
        Carregando…
      </div>
    );
  }
  if (!item) return null;

  const canAct = item.status !== "cancelled" && item.status !== "completed";

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18 }}>
        <div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 30, lineHeight: 1.05 }}>{fmtTime(item.starts_at)}</div>
          <div style={{ fontSize: 13, color: "var(--text-dim)", textTransform: "capitalize" }}>{fmtDateLong(item.starts_at)}</div>
        </div>
        <StatusBadge status={item.status} />
      </div>

      <div style={{ background: "var(--color-primary-soft)", borderRadius: 14, padding: 14, marginBottom: 12, display: "flex", alignItems: "center", gap: 12 }}>
        <Avatar name={item.client.name} size={44} color="var(--color-primary)" />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 600, fontSize: 16 }}>{item.client.name}</div>
          <div style={{ fontSize: 13, color: "var(--text-dim)" }}>{item.client.phone}</div>
        </div>
        <a href={`https://wa.me/${item.client.phone.replace(/\D/g, "")}`} target="_blank" rel="noopener noreferrer">
          <IconButton icon={<Icons.whatsapp size={18} />} style={{ background: "#E8F5E8", borderColor: "#A8D8A8", color: "#3D6B3D" }} />
        </a>
      </div>

      <Row icon={<Icons.scissors size={18} />} label="Serviço" value={
        <><strong>{item.service.name}</strong> · {item.service.duration_minutes} min</>
      } />
      <Row icon={<Icons.user size={18} />} label="Profissional" value={
        <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
          <span style={{ width: 10, height: 10, borderRadius: 999, background: memberColor(item.user.id), display: "inline-block" }} />
          {item.user.name}
        </span>
      } />
      <Row icon={<Icons.clock size={18} />} label="Término previsto" value={fmtTime(item.ends_at)} />
      {item.source === "online" && (
        <Row icon={<Icons.whatsapp size={18} />} label="Origem" value="Online" />
      )}
      {item.cancelled_by_type && (
        <Row icon={<Icons.x size={18} />} label="Cancelado por" value={
          { establishment: "Estabelecimento", client: "Cliente", system: "Sistema" }[item.cancelled_by_type] ?? item.cancelled_by_type
        } />
      )}

      {showReschedule && (
        <div style={{ marginTop: 16, padding: 14, background: "var(--bg-muted)", borderRadius: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 10 }}>Nova data e hora</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <Input label="Data" type="date" value={rescheduleDate} onChange={(e) => setRescheduleDate(e.target.value)} />
            <Input label="Hora" type="time" value={rescheduleHour} onChange={(e) => setRescheduleHour(e.target.value)} />
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
            <Button variant="secondary" onClick={() => setShowReschedule(false)} fullWidth>Cancelar</Button>
            <Button
              onClick={() => act(async () => {
                await schedulingsApi.rescheduleScheduling(eid, id, {
                  starts_at: new Date(`${rescheduleDate}T${rescheduleHour}:00`).toISOString(),
                });
                toast("Agendamento reagendado!");
                setShowReschedule(false);
              })}
              disabled={acting || !rescheduleDate || !rescheduleHour}
              fullWidth
            >
              {acting ? "Salvando…" : "Confirmar reagendamento"}
            </Button>
          </div>
        </div>
      )}

      {showCancel && (
        <div style={{ background: "var(--bg-muted)", borderRadius: 14, padding: 14, marginTop: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 10 }}>Quem está cancelando?</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {(["establishment", "client", "system"] as CancelledByType[]).map((type) => {
              const labels: Record<CancelledByType, string> = {
                establishment: "Estabelecimento", client: "Cliente", system: "Sistema",
              };
              return (
                <label
                  key={type}
                  style={{
                    display: "flex", alignItems: "center", gap: 10,
                    padding: "8px 12px", borderRadius: 10, cursor: "pointer",
                    background: cancelledBy === type ? "var(--color-primary-soft)" : "var(--surface)",
                    border: `1px solid ${cancelledBy === type ? "var(--color-primary)" : "transparent"}`,
                  }}
                >
                  <input type="radio" name="cancelledBy" checked={cancelledBy === type} onChange={() => setCancelledBy(type)} />
                  <span style={{ fontSize: 14 }}>{labels[type]}</span>
                </label>
              );
            })}
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
            <Button variant="secondary" onClick={() => setShowCancel(false)} fullWidth>Voltar</Button>
            <Button
              variant="danger"
              onClick={() => act(async () => {
                await schedulingsApi.cancelScheduling(eid, id, { cancelled_by_type: cancelledBy });
                toast("Agendamento cancelado");
                setShowCancel(false);
              })}
              disabled={acting}
              fullWidth
            >
              {acting ? "Cancelando…" : "Confirmar cancelamento"}
            </Button>
          </div>
        </div>
      )}

      {logs.length > 0 && (
        <div style={{ marginTop: 18 }}>
          <div style={{ fontSize: 12, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>Histórico</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {logs.map((log) => (
              <div key={log.id} style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "8px 12px", background: "var(--bg-muted)", borderRadius: 10, fontSize: 13,
              }}>
                <div>
                  <div style={{ fontWeight: 500 }}>
                    {log.from_status ? `${LOG_LABELS[log.from_status] ?? log.from_status} → ` : ""}
                    {LOG_LABELS[log.to_status] ?? log.to_status}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--text-dim)" }}>
                    {LOG_SOURCE[log.changed_by_source] ?? log.changed_by_source}
                  </div>
                  {log.note && <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 2 }}>{log.note}</div>}
                </div>
                <div style={{ fontSize: 11, color: "var(--text-dim)", textAlign: "right", flexShrink: 0 }}>
                  <div>{fmtDate(log.changed_at)}</div>
                  <div>{fmtTime(log.changed_at)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!showReschedule && !showCancel && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 22 }}>
          {item.status === "pending" && (
            <Button
              onClick={() => act(async () => {
                await schedulingsApi.confirmScheduling(eid, id);
                toast("Agendamento confirmado!");
              })}
              disabled={acting}
              icon={<Icons.check size={16} />}
            >
              Confirmar
            </Button>
          )}
          {item.status === "confirmed" && (
            <Button
              variant="soft"
              onClick={() => act(async () => {
                await schedulingsApi.completeScheduling(eid, id);
                toast("Agendamento concluído!");
              })}
              disabled={acting}
              icon={<Icons.check size={16} />}
            >
              Concluído
            </Button>
          )}
          {canAct && (
            <Button variant="secondary" onClick={() => setShowReschedule(true)} icon={<Icons.edit size={16} />}>
              Reagendar
            </Button>
          )}
          <Button
            variant="secondary"
            onClick={() => onEdit({
              id: item.id,
              client_id: item.client.id,
              service_id: item.service.id,
              user_id: item.user.id,
              scheduled_at: item.starts_at,
            })}
            icon={<Icons.edit size={16} />}
          >
            Editar
          </Button>
          {canAct && (
            <Button variant="danger" onClick={() => setShowCancel(true)}>Cancelar</Button>
          )}
        </div>
      )}
    </div>
  );
};
