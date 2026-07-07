import * as React from "react";
import { Icons } from "@/components/icons";
import { Badge, Button, Card, Input, PageHeader, Select } from "@/components/ui";
import { useToast } from "@/components/ToastProvider";
import { useAuth } from "@/store/auth";
import * as estApi from "@/api/establishments";
import type { EstablishmentUpdate } from "@/api/types";

const TIMEZONES = [
  { value: "America/Sao_Paulo", label: "America/Sao_Paulo (GMT-3)" },
  { value: "America/Manaus", label: "America/Manaus (GMT-4)" },
  { value: "America/Belem", label: "America/Belem (GMT-3)" },
  { value: "America/Fortaleza", label: "America/Fortaleza (GMT-3)" },
  { value: "America/Recife", label: "America/Recife (GMT-3)" },
];

const formatDocument = (doc: string, type: string): string => {
  const d = doc.replace(/\D/g, "");
  if (type === "cnpj")
    return d.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, "$1.$2.$3/$4-$5");
  return d.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
};

export const Settings: React.FC = () => {
  const toast = useToast();
  const { activeEstablishment, memberships, refreshEstablishment } = useAuth();

  const isAdmin = memberships.some(
    (m) => m.establishment_id === activeEstablishment?.id && m.role === "establishment_admin",
  );

  const [form, setForm] = React.useState<Partial<EstablishmentUpdate>>({});
  const [saving, setSaving] = React.useState(false);
  const [isDesktop, setIsDesktop] = React.useState(() => window.matchMedia("(min-width: 900px)").matches);

  React.useEffect(() => {
    const mq = window.matchMedia("(min-width: 900px)");
    const h = (e: MediaQueryListEvent) => setIsDesktop(e.matches);
    mq.addEventListener("change", h);
    return () => mq.removeEventListener("change", h);
  }, []);

  React.useEffect(() => {
    if (activeEstablishment) {
      setForm({
        name: activeEstablishment.name,
        timezone: activeEstablishment.timezone,
        street: activeEstablishment.street,
        number: activeEstablishment.number,
        complement: activeEstablishment.complement,
        neighborhood: activeEstablishment.neighborhood,
        city: activeEstablishment.city,
        state: activeEstablishment.state,
        zip_code: activeEstablishment.zip_code,
      });
    }
  }, [activeEstablishment]);

  const handleSave = async () => {
    if (!activeEstablishment) return;
    setSaving(true);
    try {
      await estApi.updateEstablishment(activeEstablishment.id, form);
      await refreshEstablishment();
      toast("Dados salvos com sucesso", "success");
    } catch (e: any) {
      toast(e?.message ?? "Erro ao salvar dados", "danger");
    } finally {
      setSaving(false);
    }
  };

  const set =
    (field: keyof EstablishmentUpdate) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((prev) => ({ ...prev, [field]: e.target.value }));

  if (!activeEstablishment) return null;

  const est = activeEstablishment;

  return (
    <div className="page" style={{ padding: "var(--page-pad)" }}>
      <PageHeader title="Configurações" subtitle="Dados do estabelecimento e integrações" />

      <Card style={{ marginBottom: 14 }}>
        <div style={{ fontFamily: "var(--font-display)", fontSize: 18, marginBottom: 12 }}>
          Estabelecimento
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <Input
            label="Nome"
            value={form.name ?? ""}
            onChange={set("name")}
            disabled={!isAdmin}
          />
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
            <Input
              label={est.document_type === "cnpj" ? "CNPJ" : "CPF"}
              value={formatDocument(est.document, est.document_type)}
              disabled
            />
          </div>
          <Select
            label="Fuso horário"
            value={form.timezone ?? ""}
            onChange={set("timezone")}
            options={TIMEZONES}
            disabled={!isAdmin}
          />

          <div style={{ borderTop: "1px solid var(--border)", paddingTop: 12, marginTop: 4 }}>
            <div style={{ fontSize: 13, color: "var(--text-dim)", marginBottom: 10, fontWeight: 500 }}>
              Endereço
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div style={{ display: "grid", gridTemplateColumns: isDesktop ? "1fr 90px" : "1fr", gap: 12 }}>
                <Input
                  label="Logradouro"
                  value={form.street ?? ""}
                  onChange={set("street")}
                  disabled={!isAdmin}
                />
                <Input
                  label="Número"
                  value={form.number ?? ""}
                  onChange={set("number")}
                  disabled={!isAdmin}
                />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12 }}>
                <Input
                  label="Complemento"
                  value={form.complement ?? ""}
                  onChange={set("complement")}
                  disabled={!isAdmin}
                />
                <Input
                  label="Bairro"
                  value={form.neighborhood ?? ""}
                  onChange={set("neighborhood")}
                  disabled={!isAdmin}
                />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: 12 }}>
                <Input
                  label="Cidade"
                  value={form.city ?? ""}
                  onChange={set("city")}
                  disabled={!isAdmin}
                />
                <Input
                  label="Estado"
                  value={form.state ?? ""}
                  onChange={set("state")}
                  disabled={!isAdmin}
                />
                <Input
                  label="CEP"
                  value={form.zip_code ?? ""}
                  onChange={set("zip_code")}
                  disabled={!isAdmin}
                />
              </div>
            </div>
          </div>

          {isAdmin && (
            <div style={{ display: "flex", justifyContent: isDesktop ? "flex-end" : "stretch", paddingTop: 4 }}>
              <Button onClick={handleSave} disabled={saving} fullWidth={!isDesktop}>
                {saving ? "Salvando…" : "Salvar alterações"}
              </Button>
            </div>
          )}
        </div>
      </Card>

      <Card>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontFamily: "var(--font-display)", fontSize: 18, display: "flex", alignItems: "center", gap: 8 }}>
              <Icons.google size={20} />
              Google Calendar
            </div>
            <div style={{ fontSize: 13, color: "var(--text-dim)", marginTop: 2 }}>
              Sincronize agendamentos com seu calendário Google
            </div>
          </div>
          <Badge tone="warning">Em breve</Badge>
        </div>
        <div style={{
          marginTop: 12, padding: "12px 14px",
          background: "var(--bg-muted)", borderRadius: 12,
          fontSize: 13, color: "var(--text-dim)",
        }}>
          A integração com o Google Calendar estará disponível em breve.
        </div>
      </Card>
    </div>
  );
};
