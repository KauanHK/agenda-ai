// /admin/establishments
//
// Global-admin list of every establishment in the platform. Lets the
// admin search, paginate, drill in to a detail sheet (with edit /
// activate / deactivate / delete + member list), and create new ones.

import * as React from "react";
import * as estApi from "@/api/establishments";
import * as membersApi from "@/api/members";
import * as usersApi from "@/api/users";
import { Icons } from "@/components/icons";
import {
  Avatar, Badge, Button, Card, EmptyState, FAB, Input, PageHeader,
  Select, Sheet, Toggle,
} from "@/components/ui";
import { useToast } from "@/components/ToastProvider";
import { useAuth } from "@/store/auth";
import { fmtDocument, timezoneOptions } from "@/lib/admin";
import type {
  EstablishmentCreate, EstablishmentRead, MembershipWithUser, UserRead, UserRole,
} from "@/api/types";

type Editing =
  | { mode: "create" }
  | { mode: "edit"; row: EstablishmentRead }
  | null;

const ROLE_LABEL: Record<UserRole, string> = {
  establishment_admin: "Admin",
  member: "Profissional",
};

export const AdminEstablishments: React.FC = () => {
  const [search, setSearch] = React.useState("");
  const [activeFilter, setActiveFilter] = React.useState<"all" | "active" | "inactive">("all");
  const [page, setPage] = React.useState(1);
  const [rows, setRows] = React.useState<EstablishmentRead[]>([]);
  const [total, setTotal] = React.useState(0);
  const [totalPages, setTotalPages] = React.useState(1);
  const [loading, setLoading] = React.useState(true);
  const [editing, setEditing] = React.useState<Editing>(null);
  const toast = useToast();
  const { refreshEstablishment } = useAuth();

  const reload = React.useCallback(async () => {
    setLoading(true);
    try {
      const res = await estApi.listEstablishments({
        name: search || undefined,
        page,
        size: 20,
      });
      setRows(res.data);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (e: any) {
      toast(e?.message ?? "Erro ao carregar estabelecimentos", "danger");
    } finally {
      setLoading(false);
    }
  }, [search, page, toast]);

  React.useEffect(() => {
    const t = setTimeout(reload, 250);
    return () => clearTimeout(t);
  }, [reload]);

  // Reset to page 1 when filters change.
  React.useEffect(() => { setPage(1); }, [search, activeFilter]);

  const filtered = React.useMemo(() => {
    if (activeFilter === "all") return rows;
    return rows.filter((r) => activeFilter === "active" ? r.is_active : !r.is_active);
  }, [rows, activeFilter]);

  const closeSheet = (changed: boolean) => {
    setEditing(null);
    if (changed) {
      reload();
      // Auth context caches the active establishment — keep it fresh
      // in case we just edited or activated/deactivated it.
      refreshEstablishment().catch(() => undefined);
    }
  };

  return (
    <div className="page" style={{ padding: "var(--page-pad)" }}>
      <PageHeader
        title="Estabelecimentos"
        subtitle={loading ? "carregando…" : `${total} cadastrado${total === 1 ? "" : "s"}`}
        action={
          <Button
            icon={<Icons.plus size={16} />}
            onClick={() => setEditing({ mode: "create" })}
            className="hide-on-mobile"
          >
            Novo
          </Button>
        }
      />

      <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 10, marginBottom: 16 }}>
        <Input
          placeholder="Buscar por nome…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          prefix={<Icons.search size={18} />}
        />
        <FilterPills value={activeFilter} onChange={setActiveFilter} />
      </div>

      {loading ? (
        <div style={{ padding: 40, textAlign: "center", color: "var(--text-dim)" }}>Carregando…</div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<Icons.home size={28} />}
          title={search ? "Nada encontrado" : "Nenhum estabelecimento"}
          description={search ? "Tente outro termo de busca." : "Cadastre o primeiro estabelecimento da plataforma."}
          action={!search ? <Button onClick={() => setEditing({ mode: "create" })} icon={<Icons.plus size={16} />}>Novo</Button> : undefined}
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {filtered.map((r) => (
            <Card
              key={r.id}
              padded={false}
              style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 14, padding: 14, alignItems: "center", cursor: "pointer", opacity: r.is_active ? 1 : 0.55 }}
              onClick={() => setEditing({ mode: "edit", row: r })}
            >
              <Avatar name={r.name} size={44} color="var(--color-primary)" />
              <div style={{ minWidth: 0 }}>
                <div style={{ fontWeight: 500, fontSize: 15, lineHeight: 1.2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {r.name}
                </div>
                <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 2, display: "flex", flexWrap: "wrap", gap: "2px 10px" }}>
                  <span>{fmtDocument(r.document, r.document_type)}</span>
                  <span>•</span>
                  <span>{r.city || "—"}{r.state ? `/${r.state}` : ""}</span>
                  <span>•</span>
                  <span>{r.timezone}</span>
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                {r.is_active
                  ? <Badge tone="success">Ativo</Badge>
                  : <Badge tone="danger">Inativo</Badge>}
                <Icons.chevronRight size={18} stroke="var(--text-dim)" />
              </div>
            </Card>
          ))}
        </div>
      )}

      <Pager page={page} totalPages={totalPages} onChange={setPage} />

      <div style={{ height: 80 }} />
      <FAB onClick={() => setEditing({ mode: "create" })} />

      <Sheet
        open={!!editing}
        onClose={() => closeSheet(false)}
        size="lg"
        title={editing?.mode === "edit" ? "Estabelecimento" : "Novo estabelecimento"}
      >
        {editing?.mode === "create" && (
          <EstablishmentForm onClose={(c) => closeSheet(c)} />
        )}
        {editing?.mode === "edit" && (
          <EstablishmentDetail row={editing.row} onClose={(c) => closeSheet(c)} />
        )}
      </Sheet>
    </div>
  );
};

// ---------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------

const FilterPills: React.FC<{
  value: "all" | "active" | "inactive";
  onChange: (v: "all" | "active" | "inactive") => void;
}> = ({ value, onChange }) => {
  const options: { v: "all" | "active" | "inactive"; label: string }[] = [
    { v: "all", label: "Todos" },
    { v: "active", label: "Ativos" },
    { v: "inactive", label: "Inativos" },
  ];
  return (
    <div style={{
      display: "inline-flex", background: "var(--surface)",
      border: "1px solid var(--border)", borderRadius: 12, padding: 3, height: 46,
    }}>
      {options.map((o) => (
        <button key={o.v} onClick={() => onChange(o.v)} style={{
          padding: "0 14px", borderRadius: 9, border: 0,
          background: value === o.v ? "var(--bg-muted)" : "transparent",
          color: value === o.v ? "var(--text)" : "var(--text-dim)",
          fontWeight: value === o.v ? 600 : 400,
          fontSize: 13, fontFamily: "inherit", cursor: "pointer",
        }}>{o.label}</button>
      ))}
    </div>
  );
};

const Pager: React.FC<{ page: number; totalPages: number; onChange: (p: number) => void }> = ({
  page, totalPages, onChange,
}) => {
  if (totalPages <= 1) return null;
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 12, marginTop: 16, color: "var(--text-dim)", fontSize: 13 }}>
      <button disabled={page <= 1} onClick={() => onChange(page - 1)} style={pagerBtn(page <= 1)}>
        <Icons.chevronLeft size={16} />
      </button>
      <span>página {page} de {totalPages}</span>
      <button disabled={page >= totalPages} onClick={() => onChange(page + 1)} style={pagerBtn(page >= totalPages)}>
        <Icons.chevronRight size={16} />
      </button>
    </div>
  );
};

const pagerBtn = (disabled: boolean): React.CSSProperties => ({
  width: 32, height: 32, borderRadius: 999, border: "1px solid var(--border)",
  background: "var(--surface)", color: disabled ? "var(--border)" : "var(--text)",
  cursor: disabled ? "default" : "pointer",
  display: "inline-flex", alignItems: "center", justifyContent: "center",
});

// ---------------------------------------------------------------------
// Detail (edit + activate/deactivate + delete + members)
// ---------------------------------------------------------------------

const EstablishmentDetail: React.FC<{
  row: EstablishmentRead;
  onClose: (changed: boolean) => void;
}> = ({ row, onClose }) => {
  const [tab, setTab] = React.useState<"info" | "members">("info");

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 18 }}>
        <Avatar name={row.name} size={56} color="var(--color-primary)" />
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 22, lineHeight: 1.1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{row.name}</div>
          <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 4 }}>
            {fmtDocument(row.document, row.document_type)} · {row.timezone}
          </div>
        </div>
        {row.is_active ? <Badge tone="success">Ativo</Badge> : <Badge tone="danger">Inativo</Badge>}
      </div>

      <div style={{
        display: "flex", gap: 4, padding: 4,
        background: "var(--bg-muted)", borderRadius: 12, marginBottom: 18,
      }}>
        {(["info", "members"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)} style={{
            flex: 1, padding: "8px 12px", borderRadius: 9, border: 0,
            background: tab === t ? "var(--surface)" : "transparent",
            color: tab === t ? "var(--text)" : "var(--text-dim)",
            fontWeight: tab === t ? 600 : 400, fontSize: 13,
            fontFamily: "inherit", cursor: "pointer",
          }}>{t === "info" ? "Informações" : "Membros"}</button>
        ))}
      </div>

      {tab === "info" && <EstablishmentForm initial={row} onClose={onClose} />}
      {tab === "members" && <EstablishmentMembers establishmentId={row.id} />}
    </div>
  );
};

// ---------------------------------------------------------------------
// Form (used both for create and edit)
// ---------------------------------------------------------------------

const EMPTY_FORM: EstablishmentCreate = {
  name: "",
  document: "",
  document_type: "cnpj",
  timezone: "America/Sao_Paulo",
  street: "",
  number: "",
  complement: "",
  neighborhood: "",
  city: "",
  state: "",
  zip_code: "",
};

const EstablishmentForm: React.FC<{
  initial?: EstablishmentRead;
  onClose: (changed: boolean) => void;
}> = ({ initial, onClose }) => {
  const isEdit = !!initial;
  const [form, setForm] = React.useState<EstablishmentCreate>(() => {
    if (!initial) return EMPTY_FORM;
    const { name, document, document_type, timezone, street, number, complement,
      neighborhood, city, state, zip_code } = initial;
    return { name, document, document_type, timezone, street, number, complement,
      neighborhood, city, state, zip_code };
  });
  const [saving, setSaving] = React.useState(false);
  const [confirmingDelete, setConfirmingDelete] = React.useState(false);
  const toast = useToast();
  const set = (k: keyof EstablishmentCreate, v: string) => setForm((s) => ({ ...s, [k]: v }));

  const save = async () => {
    if (!form.name.trim() || !form.document.trim()) {
      toast("Nome e documento são obrigatórios", "danger");
      return;
    }
    setSaving(true);
    try {
      if (isEdit && initial) {
        const { document_type, document, ...patch } = form;
        // document_type can't be patched per the API; document update is allowed.
        await estApi.updateEstablishment(initial.id, { ...patch, document });
        toast("Estabelecimento atualizado");
      } else {
        await estApi.createEstablishment(form);
        toast("Estabelecimento criado!");
      }
      onClose(true);
    } catch (e: any) {
      toast(e?.message ?? "Erro ao salvar", "danger");
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async () => {
    if (!initial) return;
    setSaving(true);
    try {
      if (initial.is_active) await estApi.deactivateEstablishment(initial.id);
      else await estApi.activateEstablishment(initial.id);
      toast(initial.is_active ? "Desativado" : "Ativado");
      onClose(true);
    } catch (e: any) { toast(e?.message ?? "Erro", "danger"); }
    finally { setSaving(false); }
  };

  const remove = async () => {
    if (!initial) return;
    setSaving(true);
    try {
      await estApi.deleteEstablishment(initial.id);
      toast("Estabelecimento excluído");
      onClose(true);
    } catch (e: any) { toast(e?.message ?? "Erro ao excluir", "danger"); }
    finally { setSaving(false); }
  };

  const tzOptions = timezoneOptions(form.timezone);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <Section title="Identificação">
        <Input label="Nome" value={form.name} onChange={(e) => set("name", e.target.value)} />
        <div style={{ display: "grid", gridTemplateColumns: "140px 1fr", gap: 10 }}>
          <Select
            label="Tipo"
            value={form.document_type}
            onChange={(e) => set("document_type", e.target.value)}
            options={[{ value: "cnpj", label: "CNPJ" }, { value: "cpf", label: "CPF" }]}
          />
          <Input
            label="Documento"
            value={form.document}
            onChange={(e) => set("document", e.target.value)}
            placeholder={form.document_type === "cnpj" ? "00.000.000/0000-00" : "000.000.000-00"}
          />
        </div>
        <Select
          label="Fuso horário"
          value={form.timezone}
          onChange={(e) => set("timezone", e.target.value)}
          options={tzOptions}
        />
      </Section>

      <Section title="Endereço">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 120px", gap: 10 }}>
          <Input label="Rua" value={form.street} onChange={(e) => set("street", e.target.value)} />
          <Input label="Número" value={form.number} onChange={(e) => set("number", e.target.value)} />
        </div>
        <Input label="Complemento" value={form.complement} onChange={(e) => set("complement", e.target.value)} />
        <Input label="Bairro" value={form.neighborhood} onChange={(e) => set("neighborhood", e.target.value)} />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 80px 130px", gap: 10 }}>
          <Input label="Cidade" value={form.city} onChange={(e) => set("city", e.target.value)} />
          <Input label="UF" maxLength={2} value={form.state} onChange={(e) => set("state", e.target.value.toUpperCase())} />
          <Input label="CEP" value={form.zip_code} onChange={(e) => set("zip_code", e.target.value)} placeholder="00000-000" />
        </div>
      </Section>

      {isEdit && initial && (
        <Section title="Status">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 14px", background: "var(--bg-muted)", borderRadius: 12 }}>
            <div>
              <div style={{ fontWeight: 500, fontSize: 14 }}>Estabelecimento ativo</div>
              <div style={{ fontSize: 12, color: "var(--text-dim)" }}>
                {initial.is_active ? "Operações disponíveis para os membros." : "Bloqueado — desativado pela administração."}
              </div>
            </div>
            <Toggle checked={initial.is_active} onChange={toggleActive} />
          </div>
        </Section>
      )}

      <div style={{ display: "flex", gap: 10, marginTop: 6 }}>
        {isEdit && (
          confirmingDelete ? (
            <>
              <Button variant="secondary" onClick={() => setConfirmingDelete(false)} disabled={saving}>Cancelar</Button>
              <Button variant="danger" onClick={remove} disabled={saving} fullWidth>Confirmar exclusão</Button>
            </>
          ) : (
            <>
              <Button variant="danger" onClick={() => setConfirmingDelete(true)} disabled={saving}>Excluir</Button>
              <Button onClick={save} disabled={saving} fullWidth>{saving ? "Salvando…" : "Salvar"}</Button>
            </>
          )
        )}
        {!isEdit && (
          <Button onClick={save} disabled={saving} fullWidth>{saving ? "Criando…" : "Criar estabelecimento"}</Button>
        )}
      </div>
    </div>
  );
};

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div>
    <div style={{
      fontSize: 11, color: "var(--text-dim)",
      letterSpacing: "0.06em", textTransform: "uppercase",
      marginBottom: 10, fontWeight: 600,
    }}>{title}</div>
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>{children}</div>
  </div>
);

// ---------------------------------------------------------------------
// Members tab inside the establishment detail sheet
// ---------------------------------------------------------------------

const EstablishmentMembers: React.FC<{ establishmentId: string }> = ({ establishmentId }) => {
  const [members, setMembers] = React.useState<MembershipWithUser[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [adding, setAdding] = React.useState(false);
  const [allUsers, setAllUsers] = React.useState<UserRead[]>([]);
  const [pickedUserId, setPickedUserId] = React.useState("");
  const [pickedRole, setPickedRole] = React.useState<UserRole>("member");
  const [saving, setSaving] = React.useState(false);
  const toast = useToast();

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const res = await membersApi.listMembers(establishmentId, { size: 100 });
      setMembers(res.data);
    } catch (e: any) {
      toast(e?.message ?? "Erro ao carregar membros", "danger");
    } finally { setLoading(false); }
  }, [establishmentId, toast]);

  React.useEffect(() => { load(); }, [load]);

  const openAdd = async () => {
    setAdding(true);
    setPickedUserId("");
    setPickedRole("member");
    try {
      const res = await usersApi.listUsers({ is_active: true, size: 100 });
      setAllUsers(res.data);
    } catch (e: any) { toast(e?.message ?? "Erro ao carregar usuários", "danger"); }
  };

  const submit = async () => {
    if (!pickedUserId) { toast("Selecione um usuário", "danger"); return; }
    setSaving(true);
    try {
      await membersApi.addMember(establishmentId, { user_id: pickedUserId, role: pickedRole });
      toast("Membro adicionado");
      setAdding(false);
      load();
    } catch (e: any) { toast(e?.message ?? "Erro ao adicionar", "danger"); }
    finally { setSaving(false); }
  };

  const updateRole = async (userId: string, role: UserRole) => {
    try {
      await membersApi.updateMember(establishmentId, userId, { role });
      toast("Papel atualizado");
      load();
    } catch (e: any) { toast(e?.message ?? "Erro ao atualizar", "danger"); }
  };

  const remove = async (userId: string) => {
    try {
      await membersApi.removeMember(establishmentId, userId);
      toast("Membro removido");
      load();
    } catch (e: any) { toast(e?.message ?? "Erro ao remover", "danger"); }
  };

  const candidates = React.useMemo(() => {
    const memberIds = new Set(members.map((m) => m.user.id));
    return allUsers.filter((u) => !memberIds.has(u.id));
  }, [allUsers, members]);

  if (loading) return <div style={{ padding: 24, textAlign: "center", color: "var(--text-dim)" }}>Carregando…</div>;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div style={{ fontSize: 12, color: "var(--text-dim)" }}>{members.length} membro{members.length === 1 ? "" : "s"}</div>
        <Button size="sm" icon={<Icons.plus size={14} />} onClick={openAdd}>Adicionar</Button>
      </div>

      {adding && (
        <Card style={{ marginBottom: 14, background: "var(--bg-muted)" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <Select
              label="Usuário"
              value={pickedUserId}
              onChange={(e) => setPickedUserId(e.target.value)}
              placeholder="Selecione…"
              options={candidates.map((u) => ({ value: u.id, label: `${u.name} — ${u.email}` }))}
            />
            <Select
              label="Papel"
              value={pickedRole}
              onChange={(e) => setPickedRole(e.target.value as UserRole)}
              options={[
                { value: "member", label: "Profissional" },
                { value: "establishment_admin", label: "Admin do estabelecimento" },
              ]}
            />
            <div style={{ display: "flex", gap: 8 }}>
              <Button variant="secondary" onClick={() => setAdding(false)} disabled={saving}>Cancelar</Button>
              <Button onClick={submit} disabled={saving} fullWidth>{saving ? "Adicionando…" : "Adicionar"}</Button>
            </div>
          </div>
        </Card>
      )}

      {members.length === 0 ? (
        <EmptyState icon={<Icons.users size={28} />} title="Sem membros" description="Adicione usuários para liberar o acesso." />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {members.map((m) => (
              <div key={m.id} style={{
                display: "grid", gridTemplateColumns: "auto 1fr auto auto", gap: 12, alignItems: "center",
                padding: 10, background: "var(--bg-muted)", borderRadius: 12,
              }}>
                <Avatar name={m.user.name} size={36} color="var(--color-primary)" />
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 500, fontSize: 14 }}>{m.user.name}</div>
                  <div style={{ fontSize: 12, color: "var(--text-dim)" }}>{m.user.email}</div>
                </div>
                <select
                  value={m.role}
                  onChange={(e) => updateRole(m.user.id, e.target.value as UserRole)}
                  style={{
                    appearance: "none", border: "1px solid var(--border)",
                    background: "var(--surface)", borderRadius: 999, padding: "4px 12px",
                    fontSize: 12, fontFamily: "inherit", cursor: "pointer",
                  }}
                >
                  {(["member", "establishment_admin"] as UserRole[]).map((r) => (
                    <option key={r} value={r}>{ROLE_LABEL[r]}</option>
                  ))}
                </select>
                <button onClick={() => remove(m.user.id)} title="Remover" style={{
                  width: 32, height: 32, borderRadius: 999, border: "1px solid var(--border)",
                  background: "var(--surface)", color: "#B83A3A", cursor: "pointer",
                  display: "inline-flex", alignItems: "center", justifyContent: "center",
                }}><Icons.trash size={14} /></button>
              </div>
          ))}
        </div>
      )}
    </div>
  );
};
