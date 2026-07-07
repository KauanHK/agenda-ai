import * as React from "react";
import * as templatesApi from "@/api/templates";
import { useEstablishmentId } from "@/store/auth";
import { Icons } from "@/components/icons";
import { Badge, Button, Card, IconButton, Input, PageHeader, Select, Sheet, Textarea } from "@/components/ui";
import { useToast } from "@/components/ToastProvider";
import type { MessagingTemplateRead, TemplateType } from "@/api/types";

const TYPE_LABELS: Record<TemplateType, string> = {
  confirmation: "Confirmação",
  reminder: "Lembrete",
  cancellation: "Cancelamento",
};

const TYPE_TONES: Record<TemplateType, "primary" | "success" | "danger"> = {
  confirmation: "success",
  reminder: "primary",
  cancellation: "danger",
};

export const Templates: React.FC = () => {
  const eid = useEstablishmentId();
  const [templates, setTemplates] = React.useState<MessagingTemplateRead[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [editing, setEditing] = React.useState<MessagingTemplateRead | null | "new">(null);
  const toast = useToast();

  const reload = React.useCallback(async () => {
    setLoading(true);
    try {
      const r = await templatesApi.listTemplates(eid, { size: 100 });
      setTemplates(r.data);
    } catch (e: any) {
      toast(e?.message ?? "Erro ao carregar templates", "danger");
    } finally {
      setLoading(false);
    }
  }, [eid, toast]);

  React.useEffect(() => { reload(); }, [reload]);

  const handleDelete = async (t: MessagingTemplateRead) => {
    if (!confirm(`Excluir template "${t.name}"?`)) return;
    try {
      await templatesApi.deleteTemplate(eid, t.id);
      toast("Template excluído");
      reload();
    } catch (e: any) {
      toast(e?.message ?? "Erro ao excluir", "danger");
    }
  };

  return (
    <div className="page" style={{ padding: "var(--page-pad)" }}>
      <PageHeader
        title="Templates"
        subtitle="Mensagens automáticas via WhatsApp"
        action={<Button icon={<Icons.plus size={16} />} onClick={() => setEditing("new")}>Novo</Button>}
      />

      {loading ? (
        <div style={{ padding: 32, textAlign: "center", color: "var(--text-dim)" }}>Carregando…</div>
      ) : templates.length === 0 ? (
        <div style={{ padding: 32, textAlign: "center", color: "var(--text-dim)" }}>Nenhum template cadastrado</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {templates.map((t) => (
            <Card key={t.id} style={{ opacity: t.is_active ? 1 : 0.5 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                    <div style={{ fontWeight: 600, fontSize: 15 }}>{t.name}</div>
                    <Badge tone={TYPE_TONES[t.type]}>{TYPE_LABELS[t.type]}</Badge>
                    {t.minutes_before != null && (
                      <Badge>{t.minutes_before} min antes</Badge>
                    )}
                    {!t.is_active && <Badge tone="neutral">Inativo</Badge>}
                  </div>
                  <div style={{
                    fontSize: 13, color: "var(--text-dim)", marginTop: 8, lineHeight: 1.5,
                    padding: "10px 12px", background: "var(--bg-muted)", borderRadius: 10, whiteSpace: "pre-wrap",
                  }}>
                    {t.content}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 6 }}>
                  <IconButton icon={<Icons.edit size={16} />} onClick={() => setEditing(t)} />
                  <IconButton icon={<Icons.trash size={16} />} onClick={() => handleDelete(t)} />
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Sheet
        open={editing !== null}
        onClose={() => setEditing(null)}
        title={editing === "new" ? "Novo template" : "Editar template"}
      >
        {editing !== null && (
          <TemplateForm
            eid={eid}
            initial={editing === "new" ? null : editing}
            onClose={() => { setEditing(null); reload(); }}
          />
        )}
      </Sheet>
    </div>
  );
};

interface TemplateFormProps {
  eid: string;
  initial: MessagingTemplateRead | null;
  onClose: () => void;
}

const TemplateForm: React.FC<TemplateFormProps> = ({ eid, initial, onClose }) => {
  const [name, setName] = React.useState(initial?.name ?? "");
  const [content, setContent] = React.useState(initial?.content ?? "");
  const [type, setType] = React.useState<TemplateType>(initial?.type ?? "confirmation");
  const [minutesBefore, setMinutesBefore] = React.useState<string>(
    initial?.minutes_before != null ? String(initial.minutes_before) : ""
  );
  const [isActive, setIsActive] = React.useState(initial?.is_active !== false);
  const [saving, setSaving] = React.useState(false);
  const toast = useToast();
  const isEdit = !!initial?.id;

  const submit = async () => {
    if (!name.trim() || !content.trim()) {
      toast("Nome e mensagem obrigatórios", "danger");
      return;
    }
    setSaving(true);
    try {
      const minutesBeforeVal = minutesBefore !== "" ? Number(minutesBefore) : null;

      if (isEdit && initial?.id) {
        await templatesApi.updateTemplate(eid, initial.id, {
          name, content, type,
          minutes_before: minutesBeforeVal,
          is_active: isActive,
        });
      } else {
        await templatesApi.createTemplate(eid, {
          name, content, type,
          minutes_before: minutesBeforeVal,
        });
      }

      toast("Template salvo!");
      onClose();
    } catch (e: any) {
      toast(e?.message ?? "Erro ao salvar", "danger");
    } finally {
      setSaving(false);
    }
  };

  const insert = (v: string) => setContent((c) => c + `{${v}}`);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Input label="Nome do template" value={name} onChange={(e) => setName(e.target.value)} />

      <Select
        label="Tipo"
        value={type}
        onChange={(e) => setType(e.target.value as TemplateType)}
        options={[
          { value: "confirmation", label: "Confirmação" },
          { value: "reminder", label: "Lembrete" },
          { value: "cancellation", label: "Cancelamento" },
        ]}
      />

      <Input
        label="Minutos antes (opcional)"
        type="number"
        min={0}
        value={minutesBefore}
        onChange={(e) => setMinutesBefore(e.target.value)}
        placeholder="Ex: 60"
      />

      <Textarea
        label="Mensagem"
        rows={5}
        value={content}
        onChange={(e) => setContent(e.target.value)}
      />

      <div>
        <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 6 }}>Variáveis</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {["cliente", "servico", "data", "hora", "profissional"].map((v) => (
            <button
              key={v}
              onClick={() => insert(v)}
              style={{
                padding: "4px 10px", borderRadius: 999, background: "var(--bg-muted)",
                border: "1px solid var(--border)", fontSize: 12,
                fontFamily: "var(--font-mono)", cursor: "pointer",
              }}
            >
              {`{${v}}`}
            </button>
          ))}
        </div>
      </div>

      {isEdit && (
        <label style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", background: "var(--bg-muted)", borderRadius: 12 }}>
          <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
          <span style={{ fontSize: 14 }}>Template ativo</span>
        </label>
      )}

      <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
        <Button variant="secondary" onClick={onClose} fullWidth>Cancelar</Button>
        <Button onClick={submit} fullWidth disabled={saving}>{saving ? "Salvando…" : "Salvar"}</Button>
      </div>
    </div>
  );
};
