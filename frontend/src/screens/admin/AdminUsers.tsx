// /admin/users
//
// Global-admin list of every user in the platform. From here an admin
// can search, paginate, create new users (assigning a role + an
// establishment in one step), edit profile fields, activate / deactivate,
// and delete.

import * as React from "react";
import * as usersApi from "@/api/users";
import * as estApi from "@/api/establishments";
import { Icons } from "@/components/icons";
import {
  Avatar, Badge, Button, Card, EmptyState, FAB, Input, PageHeader,
  Select, Sheet, Toggle,
} from "@/components/ui";
import { useToast } from "@/components/ToastProvider";
import type {
  EstablishmentRead, MembershipRead, UserCreate, UserRead, UserRole,
} from "@/api/types";

type Editing =
  | { mode: "create" }
  | { mode: "edit"; row: UserRead }
  | null;

type RoleFilter = "all" | "global_admin" | "establishment_admin" | "member";
type ActiveFilter = "all" | "active" | "inactive";

const ROLE_LABEL: Record<UserRole, string> = {
  establishment_admin: "Admin",
  member: "Profissional",
};

export const AdminUsers: React.FC = () => {
  const [search, setSearch] = React.useState("");
  const [roleFilter, setRoleFilter] = React.useState<RoleFilter>("all");
  const [activeFilter, setActiveFilter] = React.useState<ActiveFilter>("all");
  const [page, setPage] = React.useState(1);
  const [rows, setRows] = React.useState<UserRead[]>([]);
  const [total, setTotal] = React.useState(0);
  const [totalPages, setTotalPages] = React.useState(1);
  const [loading, setLoading] = React.useState(true);
  const [editing, setEditing] = React.useState<Editing>(null);
  const [establishments, setEstablishments] = React.useState<EstablishmentRead[]>([]);
  const toast = useToast();

  const reload = React.useCallback(async () => {
    setLoading(true);
    try {
      const res = await usersApi.listUsers({
        q: search || undefined,
        role: roleFilter === "establishment_admin" || roleFilter === "member" ? roleFilter : undefined,
        is_active: activeFilter === "all" ? undefined : activeFilter === "active",
        page,
        size: 20,
      });
      let data = res.data;
      if (roleFilter === "global_admin") data = data.filter((u) => u.is_global_admin);
      setRows(data);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (e: any) {
      toast(e?.message ?? "Erro ao carregar usuários", "danger");
    } finally { setLoading(false); }
  }, [search, roleFilter, activeFilter, page, toast]);

  React.useEffect(() => {
    const t = setTimeout(reload, 250);
    return () => clearTimeout(t);
  }, [reload]);

  React.useEffect(() => { setPage(1); }, [search, roleFilter, activeFilter]);

  // Cache the establishments list once for the create form's selector.
  React.useEffect(() => {
    estApi.listEstablishments({ size: 100 })
      .then((p) => setEstablishments(p.data.filter((e) => e.is_active)))
      .catch(() => undefined);
  }, []);

  const closeSheet = (changed: boolean) => {
    setEditing(null);
    if (changed) reload();
  };

  return (
    <div className="page" style={{ padding: "var(--page-pad)" }}>
      <PageHeader
        title="Usuários"
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

      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 16 }}>
        <div style={{ flex: "1 1 240px", minWidth: 200 }}>
          <Input
            placeholder="Buscar por nome ou e-mail…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            prefix={<Icons.search size={18} />}
          />
        </div>
        <SegmentedControl<RoleFilter>
          value={roleFilter}
          onChange={setRoleFilter}
          options={[
            { v: "all", label: "Todos os papéis" },
            { v: "global_admin", label: "Admin global" },
            { v: "establishment_admin", label: "Admin" },
            { v: "member", label: "Profissional" },
          ]}
        />
        <SegmentedControl<ActiveFilter>
          value={activeFilter}
          onChange={setActiveFilter}
          options={[
            { v: "all", label: "Status: todos" },
            { v: "active", label: "Ativos" },
            { v: "inactive", label: "Inativos" },
          ]}
        />
      </div>

      {loading ? (
        <div style={{ padding: 40, textAlign: "center", color: "var(--text-dim)" }}>Carregando…</div>
      ) : rows.length === 0 ? (
        <EmptyState
          icon={<Icons.users size={28} />}
          title={search ? "Nada encontrado" : "Nenhum usuário"}
          description={search ? "Tente outro termo de busca." : "Crie o primeiro usuário da plataforma."}
          action={!search ? <Button onClick={() => setEditing({ mode: "create" })} icon={<Icons.plus size={16} />}>Novo</Button> : undefined}
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {rows.map((r) => (
            <Card
              key={r.id}
              padded={false}
              style={{
                display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 14,
                padding: 14, alignItems: "center", cursor: "pointer",
                opacity: r.is_active ? 1 : 0.55,
              }}
              onClick={() => setEditing({ mode: "edit", row: r })}
            >
              <Avatar name={r.name} size={44} color="var(--color-primary)" />
              <div style={{ minWidth: 0 }}>
                <div style={{ fontWeight: 500, fontSize: 15, lineHeight: 1.2 }}>
                  {r.name}
                </div>
                <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {r.email}{r.phone ? ` · ${r.phone}` : ""}
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                {r.is_global_admin && <Badge tone="primary">Admin global</Badge>}
                {!r.is_active && <Badge tone="danger">Inativo</Badge>}
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
        size="md"
        title={editing?.mode === "edit" ? "Usuário" : "Novo usuário"}
      >
        {editing?.mode === "create" && (
          <UserCreateForm establishments={establishments} onClose={(c) => closeSheet(c)} />
        )}
        {editing?.mode === "edit" && (
          <UserEditForm row={editing.row} onClose={(c) => closeSheet(c)} />
        )}
      </Sheet>
    </div>
  );
};

// ---------------------------------------------------------------------
// Tiny helpers
// ---------------------------------------------------------------------

function SegmentedControl<T extends string>({
  value, onChange, options,
}: {
  value: T;
  onChange: (v: T) => void;
  options: { v: T; label: string }[];
}) {
  return (
    <div style={{
      display: "inline-flex", background: "var(--surface)",
      border: "1px solid var(--border)", borderRadius: 12, padding: 3, height: 46,
    }}>
      {options.map((o) => (
        <button key={o.v} onClick={() => onChange(o.v)} style={{
          padding: "0 12px", borderRadius: 9, border: 0,
          background: value === o.v ? "var(--bg-muted)" : "transparent",
          color: value === o.v ? "var(--text)" : "var(--text-dim)",
          fontWeight: value === o.v ? 600 : 400,
          fontSize: 12, fontFamily: "inherit", cursor: "pointer",
          whiteSpace: "nowrap",
        }}>{o.label}</button>
      ))}
    </div>
  );
}

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
// Create form — POST /auth/
// ---------------------------------------------------------------------

const UserCreateForm: React.FC<{
  establishments: EstablishmentRead[];
  onClose: (changed: boolean) => void;
}> = ({ establishments, onClose }) => {
  const [name, setName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [role, setRole] = React.useState<UserRole>("member");
  const [estId, setEstId] = React.useState("");
  const [showPwd, setShowPwd] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const toast = useToast();

  const submit = async () => {
    if (!name.trim() || !email.trim() || !password) {
      toast("Preencha nome, e-mail e senha", "danger"); return;
    }
    if (password.length < 8) {
      toast("A senha precisa ter ao menos 8 caracteres", "danger"); return;
    }
    if (!estId) {
      toast("Selecione um estabelecimento", "danger"); return;
    }
    setSaving(true);
    try {
      const body: UserCreate = { name, email, password, role, establishment_id: estId };
      // POST /auth/ creates the user + membership in one step.
      const { api } = await import("@/api/client");
      await api.post<UserRead>("/auth/", body);
      toast("Usuário criado!");
      onClose(true);
    } catch (e: any) {
      toast(e?.message ?? "Erro ao criar usuário", "danger");
    } finally { setSaving(false); }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Input label="Nome completo" value={name} onChange={(e) => setName(e.target.value)} />
      <Input label="E-mail" value={email} type="email" onChange={(e) => setEmail(e.target.value)} prefix={<Icons.mail size={18} />} />
      <Input
        label="Senha (mínimo 8 caracteres)"
        type={showPwd ? "text" : "password"}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        suffix={
          <button onClick={() => setShowPwd((v) => !v)} type="button" style={{ background: "transparent", border: 0, color: "var(--text-dim)", cursor: "pointer", fontSize: 12, fontFamily: "inherit" }}>
            {showPwd ? "ocultar" : "mostrar"}
          </button>
        }
      />
      <Select
        label="Papel"
        value={role}
        onChange={(e) => setRole(e.target.value as UserRole)}
        options={[
          { value: "member", label: "Profissional" },
          { value: "establishment_admin", label: "Admin do estabelecimento" },
        ]}
      />
      <Select
        label="Estabelecimento"
        value={estId}
        onChange={(e) => setEstId(e.target.value)}
        placeholder="Selecione…"
        options={establishments.map((e) => ({ value: e.id, label: e.name }))}
      />
      <div style={{ marginTop: 6 }}>
        <Button onClick={submit} disabled={saving} fullWidth>{saving ? "Criando…" : "Criar usuário"}</Button>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------
// Edit form — PATCH /users/{id} + activate/deactivate + delete
// + display memberships read from /users/{id}/memberships/
// ---------------------------------------------------------------------

const UserEditForm: React.FC<{
  row: UserRead;
  onClose: (changed: boolean) => void;
}> = ({ row, onClose }) => {
  const [name, setName] = React.useState(row.name);
  const [email, setEmail] = React.useState(row.email);
  const [phone, setPhone] = React.useState(row.phone ?? "");
  const [memberships, setMemberships] = React.useState<MembershipRead[]>([]);
  const [estsById, setEstsById] = React.useState<Record<string, EstablishmentRead>>({});
  const [saving, setSaving] = React.useState(false);
  const [confirmingDelete, setConfirmingDelete] = React.useState(false);
  const toast = useToast();

  React.useEffect(() => {
    usersApi.listUserMemberships(row.id)
      .then(async (m) => {
        setMemberships(m);
        const lookups = await Promise.allSettled(m.map((x) => estApi.getEstablishment(x.establishment_id)));
        const map: Record<string, EstablishmentRead> = {};
        lookups.forEach((l, i) => {
          if (l.status === "fulfilled") map[m[i].establishment_id] = l.value;
        });
        setEstsById(map);
      })
      .catch(() => undefined);
  }, [row.id]);

  const save = async () => {
    setSaving(true);
    try {
      await usersApi.updateUser(row.id, {
        name: name.trim() || null,
        email: email.trim() || null,
        phone: phone.trim() || null,
      });
      toast("Usuário atualizado");
      onClose(true);
    } catch (e: any) { toast(e?.message ?? "Erro ao salvar", "danger"); }
    finally { setSaving(false); }
  };

  const toggleActive = async () => {
    setSaving(true);
    try {
      if (row.is_active) await usersApi.deactivateUser(row.id);
      else await usersApi.activateUser(row.id);
      toast(row.is_active ? "Usuário desativado" : "Usuário ativado");
      onClose(true);
    } catch (e: any) { toast(e?.message ?? "Erro", "danger"); }
    finally { setSaving(false); }
  };

  const remove = async () => {
    setSaving(true);
    try {
      await usersApi.deleteUser(row.id);
      toast("Usuário excluído");
      onClose(true);
    } catch (e: any) { toast(e?.message ?? "Erro ao excluir", "danger"); }
    finally { setSaving(false); }
  };

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 18 }}>
        <Avatar name={row.name} size={56} color="var(--color-primary)" />
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 22, lineHeight: 1.1 }}>{row.name}</div>
          <div style={{ fontSize: 12, color: "var(--text-dim)" }}>{row.email}</div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 4, alignItems: "flex-end" }}>
          {row.is_global_admin && <Badge tone="primary">Admin global</Badge>}
          {row.is_active ? <Badge tone="success">Ativo</Badge> : <Badge tone="danger">Inativo</Badge>}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <Input label="Nome" value={name} onChange={(e) => setName(e.target.value)} />
        <Input label="E-mail" value={email} type="email" onChange={(e) => setEmail(e.target.value)} prefix={<Icons.mail size={18} />} />
        <Input label="Telefone" value={phone} onChange={(e) => setPhone(e.target.value)} prefix={<Icons.phone size={18} />} />
      </div>

      <div style={{ marginTop: 18 }}>
        <div style={{ fontSize: 11, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8, fontWeight: 600 }}>
          Estabelecimentos vinculados
        </div>
        {memberships.length === 0 ? (
          <div style={{ padding: 14, background: "var(--bg-muted)", borderRadius: 12, color: "var(--text-dim)", fontSize: 13 }}>
            Sem vínculos. Adicione este usuário a um estabelecimento na aba <em>Membros</em>.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {memberships.map((m) => (
              <div key={m.id} style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: "10px 14px", background: "var(--bg-muted)", borderRadius: 12,
              }}>
                <div style={{ fontSize: 14, fontWeight: 500 }}>
                  {estsById[m.establishment_id]?.name ?? m.establishment_id.slice(0, 8) + "…"}
                </div>
                <Badge tone={m.role === "establishment_admin" ? "primary" : "neutral"}>
                  {ROLE_LABEL[m.role]}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={{ marginTop: 18 }}>
        <div style={{ fontSize: 11, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8, fontWeight: 600 }}>
          Status
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 14px", background: "var(--bg-muted)", borderRadius: 12 }}>
          <div>
            <div style={{ fontWeight: 500, fontSize: 14 }}>Conta ativa</div>
            <div style={{ fontSize: 12, color: "var(--text-dim)" }}>
              {row.is_active ? "Pode acessar a plataforma." : "Login bloqueado."}
            </div>
          </div>
          <Toggle checked={row.is_active} onChange={toggleActive} />
        </div>
      </div>

      <div style={{ display: "flex", gap: 10, marginTop: 22 }}>
        {confirmingDelete ? (
          <>
            <Button variant="secondary" onClick={() => setConfirmingDelete(false)} disabled={saving}>Cancelar</Button>
            <Button variant="danger" onClick={remove} disabled={saving} fullWidth>Confirmar exclusão</Button>
          </>
        ) : (
          <>
            <Button variant="danger" onClick={() => setConfirmingDelete(true)} disabled={saving}>Excluir</Button>
            <Button onClick={save} disabled={saving} fullWidth>{saving ? "Salvando…" : "Salvar alterações"}</Button>
          </>
        )}
      </div>
    </div>
  );
};
