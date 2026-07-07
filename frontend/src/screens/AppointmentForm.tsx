import * as React from "react";
import { Icons } from "@/components/icons";
import { Avatar, Button, Input } from "@/components/ui";
import { useToast } from "@/components/ToastProvider";
import { useEstablishmentId } from "@/store/auth";
import * as clientsApi from "@/api/clients";
import * as servicesApi from "@/api/services";
import * as membersApi from "@/api/members";
import * as schedulingsApi from "@/api/schedulings";
import { fmtMoney } from "@/lib/date";
import type { ClientRead, ServiceRead } from "@/api/types";

export interface AppointmentFormInitial {
  prefillDate?: Date;
  prefillHour?: number | null;
  id?: string;
  client_id?: string;
  service_id?: string;
  user_id?: string;
  scheduled_at?: string;
  notes?: string;
}

interface TeamMember { id: string; name: string; color: string; }

function memberColor(id: string) {
  let h = 0;
  for (const c of id) h = ((h << 5) - h) + c.charCodeAt(0) | 0;
  return `hsl(${Math.abs(h) % 360},55%,45%)`;
}

export const AppointmentForm: React.FC<{
  initial: AppointmentFormInitial;
  onClose: () => void;
  onCreated?: () => void;
}> = ({ initial, onClose, onCreated }) => {
  const eid = useEstablishmentId();
  const toast = useToast();

  const [clients, setClients] = React.useState<ClientRead[]>([]);
  const [services, setServices] = React.useState<ServiceRead[]>([]);
  const [team, setTeam] = React.useState<TeamMember[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [submitting, setSubmitting] = React.useState(false);

  const [step, setStep] = React.useState(0);
  const [clientId, setClientId] = React.useState(initial?.client_id ?? "");
  const [serviceId, setServiceId] = React.useState(initial?.service_id ?? "");
  const [userId, setUserId] = React.useState(initial?.user_id ?? "");
  const [clientSearch, setClientSearch] = React.useState("");

  const initialDate = initial?.scheduled_at
    ? new Date(initial.scheduled_at)
    : (initial?.prefillDate ?? new Date());
  const initialHour = initial?.scheduled_at
    ? `${String(new Date(initial.scheduled_at).getHours()).padStart(2, "0")}:${String(new Date(initial.scheduled_at).getMinutes()).padStart(2, "0")}`
    : (initial?.prefillHour != null ? `${String(initial.prefillHour).padStart(2, "0")}:00` : "10:00");

  const [date, setDate] = React.useState(() => {
    const d = initialDate;
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  });
  const [hour, setHour] = React.useState(initialHour);
  const [notes, setNotes] = React.useState(initial?.notes ?? "");

  React.useEffect(() => {
    Promise.all([
      clientsApi.listClients(eid, { is_active: true, size: 100 }),
      servicesApi.listServices(eid, { is_active: true, size: 100 }),
      membersApi.listMembers(eid, { size: 50 }),
    ])
      .then(([cr, sr, mr]) => {
        setClients(cr.data);
        setServices(sr.data);
        const members: TeamMember[] = mr.data
          .filter((m) => m.user.is_active)
          .map((m) => ({ id: m.user.id, name: m.user.name, color: memberColor(m.user.id) }));
        setTeam(members);
        if (!initial?.user_id && members.length > 0) setUserId(members[0].id);
      })
      .catch((e: any) => toast(e?.message ?? "Erro ao carregar dados", "danger"))
      .finally(() => setLoading(false));
  }, [eid]); // eslint-disable-line react-hooks/exhaustive-deps

  const filtered = clients.filter(
    (c) =>
      c.name.toLowerCase().includes(clientSearch.toLowerCase()) ||
      c.phone.includes(clientSearch),
  );

  const service = services.find((s) => s.id === serviceId);
  const canSubmit = !!(clientId && serviceId && userId && date && hour);

  const isEdit = !!initial?.id;

  const submit = async () => {
    if (!canSubmit || submitting) return;
    setSubmitting(true);
    try {
      if (isEdit) {
        await schedulingsApi.updateScheduling(eid, initial.id!, {
          client_id: clientId,
          service_id: serviceId,
          user_id: userId,
          starts_at: new Date(`${date}T${hour}:00`).toISOString(),
        });
        toast("Agendamento atualizado!");
      } else {
        await schedulingsApi.createScheduling(eid, {
          client_id: clientId,
          service_id: serviceId,
          user_id: userId,
          starts_at: new Date(`${date}T${hour}:00`).toISOString(),
        });
        toast("Agendamento criado!");
      }
      onCreated?.();
      onClose();
    } catch (e: any) {
      toast(e?.message ?? (isEdit ? "Erro ao atualizar agendamento" : "Erro ao criar agendamento"), "danger");
    } finally {
      setSubmitting(false);
    }
  };

  const STEPS = ["Cliente", "Serviço", "Quando"];

  if (loading) {
    return (
      <div style={{ padding: "40px 0", textAlign: "center", color: "var(--text-dim)", fontSize: 14 }}>
        Carregando…
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 18 }}>
        {STEPS.map((s, i) => (
          <React.Fragment key={s}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{
                width: 24, height: 24, borderRadius: 999, fontSize: 12, fontWeight: 600,
                display: "inline-flex", alignItems: "center", justifyContent: "center",
                background: i <= step ? "var(--color-primary)" : "var(--bg-muted)",
                color: i <= step ? "white" : "var(--text-dim)",
              }}>{i < step ? "✓" : i + 1}</div>
              <span style={{ fontSize: 13, fontWeight: i === step ? 600 : 400, color: i <= step ? "var(--text)" : "var(--text-dim)" }}>{s}</span>
            </div>
            {i < STEPS.length - 1 && <div style={{ flex: 1, height: 1, background: "var(--border)" }} />}
          </React.Fragment>
        ))}
      </div>

      {step === 0 && (
        <div>
          <Input
            placeholder="Buscar cliente..."
            value={clientSearch}
            onChange={(e) => setClientSearch(e.target.value)}
            prefix={<Icons.search size={18} />}
          />
          <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 6, maxHeight: 360, overflowY: "auto" }}>
            {filtered.length === 0 && (
              <div style={{ textAlign: "center", padding: "32px 0", color: "var(--text-dim)", fontSize: 14 }}>
                {clientSearch ? "Nenhum cliente encontrado" : "Nenhum cliente cadastrado"}
              </div>
            )}
            {filtered.map((c) => {
              const sel = clientId === c.id;
              return (
                <button key={c.id} onClick={() => setClientId(c.id)} style={{
                  display: "flex", alignItems: "center", gap: 12, padding: 10, borderRadius: 12,
                  background: sel ? "var(--color-primary-soft)" : "var(--bg-muted)",
                  border: `1px solid ${sel ? "var(--color-primary)" : "transparent"}`,
                  cursor: "pointer", textAlign: "left", fontFamily: "inherit",
                }}>
                  <Avatar name={c.name} size={36} color="var(--color-primary)" />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 500, fontSize: 14 }}>{c.name}</div>
                    <div style={{ fontSize: 12, color: "var(--text-dim)" }}>{c.phone}</div>
                  </div>
                  {sel && <Icons.check size={18} />}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {step === 1 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <div style={{ fontSize: 13, color: "var(--text-dim)", marginBottom: 6, fontWeight: 500 }}>Serviço</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {services.length === 0 && (
                <div style={{ textAlign: "center", padding: "32px 0", color: "var(--text-dim)", fontSize: 14 }}>
                  Nenhum serviço cadastrado
                </div>
              )}
              {services.map((s) => {
                const sel = serviceId === s.id;
                return (
                  <button key={s.id} onClick={() => setServiceId(s.id)} style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12,
                    padding: 12, borderRadius: 12,
                    background: sel ? "var(--color-primary-soft)" : "var(--bg-muted)",
                    border: `1px solid ${sel ? "var(--color-primary)" : "transparent"}`,
                    cursor: "pointer", textAlign: "left", fontFamily: "inherit",
                  }}>
                    <div>
                      <div style={{ fontWeight: 500, fontSize: 14 }}>{s.name}</div>
                      <div style={{ fontSize: 12, color: "var(--text-dim)" }}>{s.duration_minutes} min</div>
                    </div>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>{fmtMoney(parseFloat(s.price))}</div>
                  </button>
                );
              })}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 13, color: "var(--text-dim)", marginBottom: 6, fontWeight: 500 }}>Profissional</div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {team.length === 0 && (
                <div style={{ fontSize: 13, color: "var(--text-dim)" }}>Nenhum profissional disponível</div>
              )}
              {team.map((t) => {
                const sel = userId === t.id;
                return (
                  <button key={t.id} onClick={() => setUserId(t.id)} style={{
                    display: "flex", alignItems: "center", gap: 8, padding: "8px 14px", borderRadius: 999,
                    background: sel ? "var(--color-primary-soft)" : "var(--bg-muted)",
                    border: `1px solid ${sel ? "var(--color-primary)" : "transparent"}`,
                    cursor: "pointer", fontFamily: "inherit", fontSize: 13,
                  }}>
                    <span style={{ width: 10, height: 10, borderRadius: 999, background: t.color }} />
                    {t.name.split(" ")[0]}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {step === 2 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <Input label="Data" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            <Input label="Hora" type="time" value={hour} onChange={(e) => setHour(e.target.value)} />
          </div>
          <div>
            <div style={{ fontSize: 13, color: "var(--text-dim)", marginBottom: 6, fontWeight: 500 }}>Observações</div>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="Alguma observação para o atendimento?"
              style={{ width: "100%", border: "1px solid var(--border)", background: "var(--surface)", borderRadius: 12, padding: 12, fontSize: 14, fontFamily: "inherit", outline: "none", resize: "vertical" }}
            />
          </div>
          <div style={{ background: "var(--bg-muted)", borderRadius: 14, padding: 14 }}>
            <div style={{ fontSize: 11, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>Resumo</div>
            <div style={{ fontSize: 14, lineHeight: 1.6 }}>
              <strong>{clients.find((c) => c.id === clientId)?.name}</strong><br />
              {service?.name} — {fmtMoney(parseFloat(service?.price ?? "0"))}<br />
              com {team.find((u) => u.id === userId)?.name.split(" ")[0]}
            </div>
          </div>
        </div>
      )}

      <div style={{ display: "flex", gap: 10, marginTop: 22 }}>
        {step > 0 && (
          <Button variant="secondary" onClick={() => setStep(step - 1)} fullWidth>
            Voltar
          </Button>
        )}
        {step < 2 ? (
          <Button
            onClick={() => setStep(step + 1)}
            fullWidth
            disabled={(step === 0 && !clientId) || (step === 1 && (!serviceId || !userId))}
            style={{ opacity: (step === 0 && !clientId) || (step === 1 && (!serviceId || !userId)) ? 0.5 : 1 }}
          >
            Continuar
          </Button>
        ) : (
          <Button
            onClick={submit}
            fullWidth
            disabled={!canSubmit || submitting}
            style={{ opacity: canSubmit && !submitting ? 1 : 0.5 }}
          >
            {submitting ? (isEdit ? "Salvando…" : "Criando…") : (isEdit ? "Salvar alterações" : "Confirmar agendamento")}
          </Button>
        )}
      </div>
    </div>
  );
};
