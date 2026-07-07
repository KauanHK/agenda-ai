import * as React from "react";
import * as clientsApi from "@/api/clients";
import * as schedulingsApi from "@/api/schedulings";
import { useEstablishmentId } from "@/store/auth";
import { Icons } from "@/components/icons";
import { Avatar, Button, EmptyState, FAB, Input, PageHeader, Sheet, StatusBadge } from "@/components/ui";
import { useToast } from "@/components/ToastProvider";
import { fmtDate } from "@/lib/date";
import type { ClientRead, SchedulingRead } from "@/api/types";

type Editing = (Omit<Partial<ClientRead>, 'id'> & { id: string | null }) | null;

export const Clients: React.FC = () => {
  const eid = useEstablishmentId();
  const [search, setSearch] = React.useState("");
  const [clients, setClients] = React.useState<ClientRead[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [editing, setEditing] = React.useState<Editing>(null);
  const toast = useToast();

  const reload = React.useCallback(async () => {
    setLoading(true);
    try {
      const res = await clientsApi.listClients(eid, { is_active: true, size: 100, q: search || undefined });
      setClients(res.data);
    } catch (e: any) {
      toast(e?.message ?? "Erro ao carregar clientes", "danger");
    } finally {
      setLoading(false);
    }
  }, [eid, search, toast]);

  React.useEffect(() => {
    const t = setTimeout(reload, 250);
    return () => clearTimeout(t);
  }, [reload]);

  const groups: Record<string, ClientRead[]> = {};
  clients.forEach((c) => {
    const k = (c.name[0] ?? "?").toUpperCase();
    (groups[k] = groups[k] || []).push(c);
  });
  const keys = Object.keys(groups).sort();

  return (
    <div className="page" style={{ padding: "var(--page-pad)" }}>
      <PageHeader title="Clientes" subtitle={`${clients.length} cadastrados`}
        action={<Button icon={<Icons.plus size={16} />} onClick={() => setEditing({ id: null })} className="hide-on-mobile">Novo</Button>} />

      <div style={{ marginBottom: 16 }}>
        <Input placeholder="Buscar por nome ou telefone..." value={search} onChange={(e) => setSearch(e.target.value)} prefix={<Icons.search size={18} />} />
      </div>

      {loading ? (
        <div style={{ padding: 32, textAlign: "center", color: "var(--text-dim)" }}>Carregando…</div>
      ) : clients.length === 0 ? (
        <EmptyState icon={<Icons.users size={28} />} title="Nenhum cliente" description="Cadastre seu primeiro cliente para começar." />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {keys.map((k) => (
            <div key={k}>
              <div style={{ fontSize: 12, color: "var(--text-dim)", letterSpacing: "0.05em", marginBottom: 6, fontWeight: 600 }}>{k}</div>
              <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 14, overflow: "hidden" }}>
                {groups[k].map((c, i) => (
                  <button key={c.id} onClick={() => setEditing(c)} style={{
                    display: "flex", alignItems: "center", gap: 12, width: "100%",
                    padding: 12, background: "transparent",
                    borderBottom: i < groups[k].length - 1 ? "1px solid var(--border)" : 0,
                    border: 0, cursor: "pointer", textAlign: "left", fontFamily: "inherit",
                  }}>
                    <Avatar name={c.name} size={42} color="var(--color-primary)" />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 500, fontSize: 14 }}>{c.name}</div>
                      <div style={{ fontSize: 12, color: "var(--text-dim)" }}>{c.phone}</div>
                    </div>
                    <Icons.chevronRight size={18} stroke="var(--text-dim)" />
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
      <div style={{ height: 80 }} />
      <FAB onClick={() => setEditing({ id: null })} />

      <Sheet open={!!editing} onClose={() => setEditing(null)} title={editing?.id ? "Editar cliente" : "Novo cliente"}>
        {editing && <ClientForm initial={editing} eid={eid} onClose={() => { setEditing(null); reload(); }} />}
      </Sheet>
    </div>
  );
};

const ClientForm: React.FC<{ initial: Omit<Partial<ClientRead>, 'id'> & { id: string | null }; eid: string; onClose: () => void }> = ({ initial, eid, onClose }) => {
  const isEdit = !!initial.id;
  const [name, setName] = React.useState(initial?.name || "");
  const [phone, setPhone] = React.useState(initial?.phone || "");
  const [email, setEmail] = React.useState(initial?.email || "");
  const [saving, setSaving] = React.useState(false);
  const [history, setHistory] = React.useState<SchedulingRead[]>([]);
  const toast = useToast();

  React.useEffect(() => {
    if (!isEdit || !initial.id) return;
    schedulingsApi.listSchedulings(eid, { client_id: initial.id, size: 5 })
      .then((r) => setHistory(r.data))
      .catch(() => undefined);
  }, [isEdit, initial.id, eid]);

  const submit = async () => {
    if (!name || !phone) { toast("Nome e telefone obrigatórios", "danger"); return; }
    setSaving(true);
    try {
      if (isEdit && initial.id) {
        await clientsApi.updateClient(eid, initial.id, { name, phone, email: email || null });
      } else {
        await clientsApi.createClient(eid, { name, phone, email: email || null });
      }
      toast(isEdit ? "Cliente atualizado" : "Cliente cadastrado!");
      onClose();
    } catch (e: any) {
      toast(e?.message ?? "Erro ao salvar", "danger");
    } finally { setSaving(false); }
  };

  const deactivate = async () => {
    if (!initial.id) return;
    setSaving(true);
    try {
      await clientsApi.deactivateClient(eid, initial.id);
      toast("Cliente desativado");
      onClose();
    } catch (e: any) { toast(e?.message ?? "Erro", "danger"); }
    finally { setSaving(false); }
  };

  return (
    <div>
      {isEdit && (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 18 }}>
          <Avatar name={initial.name} size={72} color="var(--color-primary)" />
          <div style={{ fontFamily: "var(--font-display)", fontSize: 22, marginTop: 10 }}>{initial.name}</div>
        </div>
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <Input label="Nome completo" value={name} onChange={(e) => setName(e.target.value)} />
        <Input label="Telefone (WhatsApp)" value={phone} onChange={(e) => setPhone(e.target.value)} prefix={<Icons.phone size={18} />} />
        <Input label="E-mail (opcional)" value={email ?? ""} onChange={(e) => setEmail(e.target.value)} prefix={<Icons.mail size={18} />} />
      </div>

      {isEdit && history.length > 0 && (
        <div style={{ marginTop: 22 }}>
          <div style={{ fontSize: 12, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>Histórico recente</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {history.map((s) => (
              <div key={s.id} style={{ padding: "10px 12px", background: "var(--bg-muted)", borderRadius: 10, fontSize: 13, display: "flex", justifyContent: "space-between" }}>
                <div style={{ fontSize: 11, color: "var(--text-dim)" }}>{fmtDate(s.starts_at)}</div>
                <StatusBadge status={s.status} />
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ display: "flex", gap: 10, marginTop: 22 }}>
        {isEdit && <Button variant="danger" onClick={deactivate} disabled={saving}>Desativar</Button>}
        <Button onClick={submit} fullWidth disabled={saving}>{saving ? "Salvando…" : isEdit ? "Salvar" : "Cadastrar"}</Button>
      </div>
    </div>
  );
};
