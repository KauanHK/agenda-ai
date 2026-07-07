import * as React from "react";
import * as servicesApi from "@/api/services";
import * as templatesApi from "@/api/templates";
import { useEstablishmentId } from "@/store/auth";
import { Icons } from "@/components/icons";
import { Badge, Button, Card, IconButton, Input, PageHeader, Select, Sheet, Textarea } from "@/components/ui";
import { useToast } from "@/components/ToastProvider";
import { fmtMoney } from "@/lib/date";
import type { MessagingTemplateRead, ServiceRead, TemplateType } from "@/api/types";

const TEMPLATE_TYPES: { type: TemplateType; label: string }[] = [
  { type: "confirmation", label: "Confirmação" },
  { type: "reminder", label: "Lembrete" },
  { type: "cancellation", label: "Cancelamento" },
];

export const Services: React.FC = () => {
  const eid = useEstablishmentId();
  const [services, setServices] = React.useState<ServiceRead[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [editing, setEditing] = React.useState<Partial<ServiceRead> | null>(null);
  const toast = useToast();

  const reload = React.useCallback(async () => {
    setLoading(true);
    try {
      const r = await servicesApi.listServices(eid, { size: 100 });
      setServices(r.data);
    } catch (e: any) { toast(e?.message ?? "Erro ao carregar", "danger"); }
    finally { setLoading(false); }
  }, [eid, toast]);

  React.useEffect(() => { reload(); }, [reload]);

  return (
    <div className="page" style={{ padding: "var(--page-pad)" }}>
      <PageHeader title="Serviços" subtitle={`${services.filter((x) => x.is_active).length} ativos`}
        action={<Button icon={<Icons.plus size={16} />} onClick={() => setEditing({})}>Novo</Button>} />

      {loading ? (
        <div style={{ padding: 32, textAlign: "center", color: "var(--text-dim)" }}>Carregando…</div>
      ) : (
        <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
          {services.map((s) => (
            <Card key={s.id} style={{ opacity: s.is_active ? 1 : 0.5 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>{s.name}</div>
                  <div style={{ fontSize: 13, color: "var(--text-dim)", marginTop: 2 }}>{s.description}</div>
                  <div style={{ display: "flex", gap: 6, marginTop: 10 }}>
                    <Badge>{s.duration_minutes} min</Badge>
                    <Badge tone="primary">{fmtMoney(Number(s.price))}</Badge>
                    {!s.is_active && <Badge tone="neutral">Inativo</Badge>}
                  </div>
                </div>
                <IconButton icon={<Icons.edit size={16} />} onClick={() => setEditing(s)} />
              </div>
            </Card>
          ))}
        </div>
      )}

      <Sheet open={!!editing} onClose={() => setEditing(null)} title={editing?.id ? "Editar serviço" : "Novo serviço"}>
        {editing && <ServiceForm initial={editing} eid={eid} onClose={() => { setEditing(null); reload(); }} />}
      </Sheet>
    </div>
  );
};

const ServiceForm: React.FC<{ initial: Partial<ServiceRead>; eid: string; onClose: () => void }> = ({ initial, eid, onClose }) => {
  const [name, setName] = React.useState(initial?.name || "");
  const [description, setDescription] = React.useState(initial?.description || "");
  const [duration, setDuration] = React.useState(initial?.duration_minutes || 30);
  const [price, setPrice] = React.useState(Number(initial?.price ?? 0));
  const [isActive, setIsActive] = React.useState(initial?.is_active !== false);
  const [saving, setSaving] = React.useState(false);

  // templates[type] -> all active templates of that type
  const [templatesByType, setTemplatesByType] = React.useState<Record<TemplateType, MessagingTemplateRead[]>>({
    confirmation: [], reminder: [], cancellation: [],
  });
  // selectedTemplateId[type] -> currently selected template id (or "" for none)
  const [selectedTemplateId, setSelectedTemplateId] = React.useState<Record<TemplateType, string>>({
    confirmation: "", reminder: "", cancellation: "",
  });
  // originalTemplateId[type] -> what was linked when the sheet opened
  const [originalTemplateId, setOriginalTemplateId] = React.useState<Record<TemplateType, string>>({
    confirmation: "", reminder: "", cancellation: "",
  });

  const toast = useToast();
  const isEdit = !!initial?.id;

  React.useEffect(() => {
    if (!isEdit) return;
    templatesApi.listTemplates(eid, { is_active: true, size: 100 })
      .then((r) => {
        const byType: Record<TemplateType, MessagingTemplateRead[]> = {
          confirmation: [], reminder: [], cancellation: [],
        };
        for (const t of r.data) byType[t.type].push(t);
        setTemplatesByType(byType);
      })
      .catch(() => {});

    templatesApi.listTemplates(eid, { service_id: initial.id, size: 100 })
      .then((r) => {
        const sel: Record<TemplateType, string> = { confirmation: "", reminder: "", cancellation: "" };
        for (const t of r.data) sel[t.type] = t.id;
        setSelectedTemplateId(sel);
        setOriginalTemplateId(sel);
      })
      .catch(() => {});
  }, [eid, isEdit, initial?.id]);

  const submit = async () => {
    if (!name) { toast("Nome obrigatório", "danger"); return; }
    setSaving(true);
    try {
      if (isEdit && initial.id) {
        await servicesApi.updateService(eid, initial.id, {
          name, description: description || null, duration_minutes: Number(duration),
          price: Number(price), is_active: isActive,
        });

        const sid = initial.id;
        const ops: Promise<void>[] = [];
        for (const { type } of TEMPLATE_TYPES) {
          const prev = originalTemplateId[type];
          const next = selectedTemplateId[type];
          if (prev === next) continue;
          if (prev) ops.push(templatesApi.unlinkService(eid, prev, sid));
          if (next) ops.push(templatesApi.linkService(eid, next, sid));
        }
        await Promise.all(ops);
      } else {
        await servicesApi.createService(eid, {
          name, description: description || null,
          duration_minutes: Number(duration), price: Number(price),
        });
      }
      toast("Serviço salvo!");
      onClose();
    } catch (e: any) { toast(e?.message ?? "Erro", "danger"); }
    finally { setSaving(false); }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Input label="Nome" value={name} onChange={(e) => setName(e.target.value)} />
      <Textarea label="Descrição" value={description ?? ""} onChange={(e) => setDescription(e.target.value)} />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <Input label="Duração (min)" type="number" value={duration} onChange={(e) => setDuration(Number(e.target.value))} />
        <Input label="Preço (R$)" type="number" step="0.01" value={price} onChange={(e) => setPrice(Number(e.target.value))} />
      </div>
      {isEdit && (
        <>
          <label style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", background: "var(--bg-muted)", borderRadius: 12 }}>
            <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
            <span style={{ fontSize: 14 }}>Serviço ativo no catálogo</span>
          </label>

          <div style={{ borderTop: "1px solid var(--border)", paddingTop: 12, display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text-dim)" }}>Notificações automáticas</div>
            {TEMPLATE_TYPES.map(({ type, label }) => (
              <Select
                key={type}
                label={label}
                value={selectedTemplateId[type]}
                onChange={(e) => setSelectedTemplateId((prev) => ({ ...prev, [type]: e.target.value }))}
                placeholder="Nenhum"
                options={templatesByType[type].map((t) => ({ value: t.id, label: t.name }))}
              />
            ))}
          </div>
        </>
      )}
      <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
        <Button variant="secondary" onClick={onClose} fullWidth>Cancelar</Button>
        <Button onClick={submit} fullWidth disabled={saving}>{saving ? "Salvando…" : "Salvar"}</Button>
      </div>
    </div>
  );
};
