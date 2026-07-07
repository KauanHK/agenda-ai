import * as React from "react";
import * as notificationsApi from "@/api/notifications";
import * as templatesApi from "@/api/templates";
import { useEstablishmentId } from "@/store/auth";
import { Icons } from "@/components/icons";
import { Badge, Button, Card, EmptyState, Input, PageHeader, Select, Sheet, Textarea } from "@/components/ui";
import { useToast } from "@/components/ToastProvider";
import { fmtDate, fmtTime } from "@/lib/date";
import type { MessagingTemplateRead, NotificationStatus, SchedulingNotificationRead } from "@/api/types";

const NOTIF_STATUS: Record<NotificationStatus, { label: string; tone: "warning" | "success" | "neutral" | "danger" }> = {
  pending: { label: "Pendente", tone: "warning" },
  sent: { label: "Enviada", tone: "success" },
  cancelled: { label: "Cancelada", tone: "neutral" },
  failed: { label: "Falhou", tone: "danger" },
};

const NotifBadge: React.FC<{ status: NotificationStatus }> = ({ status }) => {
  const s = NOTIF_STATUS[status];
  return <Badge tone={s.tone}>{s.label}</Badge>;
};

const fmtDateTime = (iso: string | null) => {
  if (!iso) return "—";
  return `${fmtDate(iso)} ${fmtTime(iso)}`;
};

const truncId = (id: string | null) => (id ? `${id.slice(0, 8)}…` : "—");

interface Filters {
  status: NotificationStatus | "";
  template_id: string;
  sent_at_from: string;
  sent_at_to: string;
}

const EMPTY_FILTERS: Filters = {
  status: "",
  template_id: "",
  sent_at_from: "",
  sent_at_to: "",
};

export const Notifications: React.FC = () => {
  const eid = useEstablishmentId();
  const toast = useToast();

  const [items, setItems] = React.useState<SchedulingNotificationRead[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [page, setPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const [total, setTotal] = React.useState(0);
  const [detail, setDetail] = React.useState<SchedulingNotificationRead | null>(null);
  const [cancelling, setCancelling] = React.useState<string | null>(null);
  const [filters, setFilters] = React.useState<Filters>(EMPTY_FILTERS);
  const [templates, setTemplates] = React.useState<MessagingTemplateRead[]>([]);

  const load = React.useCallback(async (p: number, f: Filters) => {
    setLoading(true);
    try {
      const r = await notificationsApi.listNotifications(eid, {
        status: f.status || undefined,
        template_id: f.template_id || undefined,
        sent_at_from: f.sent_at_from || undefined,
        sent_at_to: f.sent_at_to || undefined,
        page: p,
        size: 10,
      });
      setItems(r.data);
      setPage(r.page);
      setTotalPages(r.total_pages);
      setTotal(r.total);
    } catch (e: any) {
      toast(e?.message ?? "Erro ao carregar notificações", "danger");
    } finally {
      setLoading(false);
    }
  }, [eid, toast]);

  React.useEffect(() => {
    templatesApi.listTemplates(eid, { size: 100 }).then((r) => setTemplates(r.data)).catch(() => {});
  }, [eid]);

  React.useEffect(() => {
    load(1, filters);
  }, [eid, filters]); // eslint-disable-line react-hooks/exhaustive-deps

  const setFilter = <K extends keyof Filters>(key: K, value: Filters[K]) =>
    setFilters((prev) => ({ ...prev, [key]: value }));

  const goPage = (p: number) => load(p, filters);

  const handleCancel = async (n: SchedulingNotificationRead) => {
    if (!confirm("Cancelar esta notificação?")) return;
    setCancelling(n.id);
    try {
      const updated = await notificationsApi.cancelNotification(eid, n.id);
      setItems((prev) => prev.map((item) => (item.id === n.id ? updated : item)));
      if (detail?.id === n.id) setDetail(updated);
      toast("Notificação cancelada");
    } catch (e: any) {
      toast(e?.message ?? "Erro ao cancelar", "danger");
    } finally {
      setCancelling(null);
    }
  };

  const openDetail = async (n: SchedulingNotificationRead) => {
    setDetail(n);
    try {
      const fresh = await notificationsApi.getNotification(eid, n.id);
      setDetail(fresh);
    } catch { /* usa snapshot da lista */ }
  };

  const hasFilters = Object.values(filters).some(Boolean);

  return (
    <div className="page" style={{ padding: "var(--page-pad)" }}>
      <PageHeader
        title="Notificações"
        subtitle={loading ? "…" : `${total} registro${total === 1 ? "" : "s"}`}
      />

      {/* Filtros */}
      <div style={{
        background: "var(--surface)", border: "1px solid var(--border)",
        borderRadius: "var(--radius)", padding: "14px 16px", marginBottom: 16,
      }}>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "flex-end" }}>
          <div style={{ flex: "1 1 150px" }}>
            <Select
              label="Status"
              value={filters.status}
              onChange={(e) => setFilter("status", e.target.value as NotificationStatus | "")}
              placeholder="Todos"
              options={[
                { value: "pending", label: "Pendente" },
                { value: "sent", label: "Enviada" },
                { value: "cancelled", label: "Cancelada" },
                { value: "failed", label: "Falhou" },
              ]}
            />
          </div>
          <div style={{ flex: "1 1 200px" }}>
            <Select
              label="Template"
              value={filters.template_id}
              onChange={(e) => setFilter("template_id", e.target.value)}
              placeholder="Todos"
              options={templates.map((t) => ({ value: t.id, label: t.name }))}
            />
          </div>
          <div style={{ flex: "1 1 170px" }}>
            <Input
              label="Enviada de"
              type="datetime-local"
              value={filters.sent_at_from}
              onChange={(e) => setFilter("sent_at_from", e.target.value)}
            />
          </div>
          <div style={{ flex: "1 1 170px" }}>
            <Input
              label="Enviada até"
              type="datetime-local"
              value={filters.sent_at_to}
              onChange={(e) => setFilter("sent_at_to", e.target.value)}
            />
          </div>
          {hasFilters && (
            <div style={{ paddingBottom: 1 }}>
              <Button variant="ghost" size="sm" onClick={() => setFilters(EMPTY_FILTERS)}>
                Limpar filtros
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Lista */}
      {loading ? (
        <div style={{ padding: 32, textAlign: "center", color: "var(--text-dim)" }}>Carregando…</div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={<Icons.bell size={28} />}
          title="Nenhuma notificação"
          description="Nenhuma notificação encontrada para os filtros selecionados."
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {items.map((n) => (
            <Card key={n.id} onClick={() => openDetail(n)} style={{ cursor: "pointer" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                    <NotifBadge status={n.status} />
                    <span style={{ fontSize: 13, color: "var(--text-dim)" }}>
                      {fmtDateTime(n.scheduled_at)}
                    </span>
                    <span style={{ fontSize: 12, color: "var(--text-dim)" }}>
                      {n.attempts} tentativa{n.attempts !== 1 ? "s" : ""}
                    </span>
                  </div>
                  <div style={{ display: "flex", gap: 14, marginTop: 4, flexWrap: "wrap" }}>
                    {n.sent_at && (
                      <span style={{ fontSize: 12, color: "var(--text-dim)" }}>
                        Enviada: {fmtDateTime(n.sent_at)}
                      </span>
                    )}
                    {n.template_id && (
                      <span style={{ fontSize: 12, color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                        Template: {truncId(n.template_id)}
                      </span>
                    )}
                  </div>
                  {n.status === "failed" && n.last_error && (
                    <div style={{ fontSize: 12, color: "#8C2E2E", marginTop: 4 }}>⚠ {n.last_error}</div>
                  )}
                </div>
                {n.status === "pending" && (
                  <Button
                    variant="danger"
                    size="sm"
                    disabled={cancelling === n.id}
                    onClick={(e) => { e.stopPropagation(); handleCancel(n); }}
                  >
                    {cancelling === n.id ? "…" : "Cancelar"}
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Paginação */}
      {!loading && totalPages > 1 && (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 12, marginTop: 20 }}>
          <Button
            variant="secondary"
            size="sm"
            disabled={page <= 1}
            onClick={() => goPage(page - 1)}
            icon={<Icons.chevronLeft size={16} />}
          >
            Anterior
          </Button>
          <span style={{ fontSize: 14, color: "var(--text-dim)", minWidth: 60, textAlign: "center" }}>
            {page} / {totalPages}
          </span>
          <Button
            variant="secondary"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => goPage(page + 1)}
          >
            Próxima
          </Button>
        </div>
      )}

      {/* Sheet de detalhe */}
      <Sheet open={!!detail} onClose={() => setDetail(null)} title="Detalhes da notificação" size="md">
        {detail && (
          <NotificationDetail
            notification={detail}
            onCancel={handleCancel}
            cancelling={cancelling === detail.id}
          />
        )}
      </Sheet>
    </div>
  );
};

const Field: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <div>
    <div style={{
      fontSize: 11, color: "var(--text-dim)", fontWeight: 600,
      textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 3,
    }}>
      {label}
    </div>
    <div style={{ fontSize: 14 }}>{children}</div>
  </div>
);

const Mono: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, wordBreak: "break-all" }}>{children}</span>
);

interface NotificationDetailProps {
  notification: SchedulingNotificationRead;
  onCancel: (n: SchedulingNotificationRead) => void;
  cancelling: boolean;
}

const NotificationDetail: React.FC<NotificationDetailProps> = ({ notification: n, onCancel, cancelling }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <NotifBadge status={n.status} />
      <span style={{ fontSize: 13, color: "var(--text-dim)" }}>
        agendada para {fmtDateTime(n.scheduled_at)}
      </span>
    </div>

    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
      <Field label="ID"><Mono>{n.id}</Mono></Field>
      <Field label="Tentativas">{n.attempts}</Field>
      <Field label="Agendamento"><Mono>{n.scheduling_id}</Mono></Field>
      <Field label="Template"><Mono>{n.template_id ?? "—"}</Mono></Field>
      <Field label="Agendada para">{fmtDateTime(n.scheduled_at)}</Field>
      <Field label="Enviada em">{fmtDateTime(n.sent_at)}</Field>
      <Field label="Última tentativa">{fmtDateTime(n.last_attempt_at)}</Field>
      <Field label="Atualizada em">{fmtDateTime(n.updated_at)}</Field>
    </div>

    {n.status === "failed" && n.last_error && (
      <div style={{
        padding: "12px 14px", background: "#FEF2F2",
        border: "1px solid #FECACA", borderRadius: 10,
      }}>
        <div style={{ fontWeight: 600, fontSize: 13, color: "#8C2E2E", marginBottom: 6 }}>
          ⚠ Último erro
        </div>
        <div style={{
          fontFamily: "var(--font-mono)", fontSize: 12,
          color: "#8C2E2E", whiteSpace: "pre-wrap", wordBreak: "break-all",
        }}>
          {n.last_error}
        </div>
      </div>
    )}

    {n.content_at_send && (
      <Textarea
        label="Conteúdo enviado"
        value={n.content_at_send}
        readOnly
        rows={5}
        style={{ opacity: 0.85, cursor: "default" }}
      />
    )}

    {n.status === "pending" && (
      <Button variant="danger" fullWidth disabled={cancelling} onClick={() => onCancel(n)}>
        {cancelling ? "Cancelando…" : "Cancelar notificação"}
      </Button>
    )}
  </div>
);
