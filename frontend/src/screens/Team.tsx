import * as React from "react";
import * as membersApi from "@/api/members";
import * as usersApi from "@/api/users";
import { useEstablishmentId } from "@/store/auth";
import { Icons } from "@/components/icons";
import { Avatar, Badge, Button, Card, EmptyState, FAB, Input, PageHeader, Sheet } from "@/components/ui";
import { useToast } from "@/components/ToastProvider";
import type { MembershipWithUser } from "@/api/types";

const ROLE_LABEL: Record<string, string> = {
  establishment_admin: "Admin",
  member: "Profissional",
};

export const Team: React.FC = () => {
  const eid = useEstablishmentId();
  const [members, setMembers] = React.useState<MembershipWithUser[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [creating, setCreating] = React.useState(false);
  const [selected, setSelected] = React.useState<MembershipWithUser | null>(null);
  const toast = useToast();

  const reload = React.useCallback(async () => {
    setLoading(true);
    try {
      const res = await membersApi.listMembers(eid, { page: 1, size: 100 });
      setMembers(res.data);
    } catch (e: any) {
      toast(e?.message ?? "Erro ao carregar equipe", "danger");
    } finally {
      setLoading(false);
    }
  }, [eid, toast]);

  React.useEffect(() => { reload(); }, [reload]);

  const activeCount = members.filter((m) => m.is_active).length;

  return (
    <div className="page" style={{ padding: "var(--page-pad)" }}>
      <PageHeader
        title="Equipe"
        subtitle={`${activeCount} membros ativos`}
        action={
          <Button icon={<Icons.plus size={16} />} onClick={() => setCreating(true)} className="hide-on-mobile">
            Novo
          </Button>
        }
      />

      {loading ? (
        <div style={{ padding: 32, textAlign: "center", color: "var(--text-dim)" }}>Carregando…</div>
      ) : members.length === 0 ? (
        <EmptyState
          icon={<Icons.users size={28} />}
          title="Nenhum membro"
          description="Cadastre o primeiro profissional da equipe."
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {members.map((m) => (
            <Card
              key={m.id}
              style={{ display: "flex", alignItems: "center", gap: 14, opacity: m.is_active ? 1 : 0.5, cursor: "pointer" }}
              onClick={() => setSelected(m)}
            >
              <Avatar name={m.user.name} size={48} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 500, fontSize: 15 }}>{m.user.name}</div>
                <div style={{ fontSize: 13, color: "var(--text-dim)" }}>{m.user.email}</div>
              </div>
              <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                <Badge tone={m.role === "establishment_admin" ? "primary" : "neutral"}>
                  {ROLE_LABEL[m.role] ?? m.role}
                </Badge>
                {!m.is_active && <Badge>Inativo</Badge>}
              </div>
            </Card>
          ))}
        </div>
      )}

      <div style={{ height: 80 }} />
      <FAB onClick={() => setCreating(true)} />

      <Sheet open={creating} onClose={() => setCreating(false)} title="Novo membro">
        <CreateMemberForm
          eid={eid}
          onClose={() => { setCreating(false); reload(); }}
        />
      </Sheet>

      <Sheet open={!!selected} onClose={() => setSelected(null)} title="Membro">
        {selected && (
          <MemberDetail
            member={selected}
            eid={eid}
            onClose={() => { setSelected(null); reload(); }}
          />
        )}
      </Sheet>
    </div>
  );
};

const CreateMemberForm: React.FC<{ eid: string; onClose: () => void }> = ({ eid, onClose }) => {
  const [name, setName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [phone, setPhone] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [saving, setSaving] = React.useState(false);
  const toast = useToast();

  const submit = async () => {
    if (!name.trim() || !email.trim() || !password) {
      toast("Nome, e-mail e senha são obrigatórios", "danger");
      return;
    }
    if (password.length < 8) {
      toast("A senha deve ter no mínimo 8 caracteres", "danger");
      return;
    }
    if (password !== confirmPassword) {
      toast("As senhas não coincidem", "danger");
      return;
    }
    setSaving(true);
    try {
      await usersApi.createUser({
        name: name.trim(),
        email: email.trim(),
        phone: phone.trim() || null,
        password,
        role: "member",
        establishment_id: eid,
      });
      toast("Membro cadastrado!");
      onClose();
    } catch (e: any) {
      toast(e?.message ?? "Erro ao cadastrar membro", "danger");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Input
        label="Nome completo"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <Input
        label="E-mail"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        prefix={<Icons.mail size={18} />}
      />
      <Input
        label="Telefone (opcional)"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        prefix={<Icons.phone size={18} />}
      />
      <Input
        label="Senha"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        hint="Mínimo 8 caracteres"
      />
      <Input
        label="Confirmar senha"
        type="password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
      />
      <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
        <Button variant="secondary" onClick={onClose} fullWidth>Cancelar</Button>
        <Button onClick={submit} fullWidth disabled={saving}>
          {saving ? "Cadastrando…" : "Cadastrar"}
        </Button>
      </div>
    </div>
  );
};

const MemberDetail: React.FC<{
  member: MembershipWithUser;
  eid: string;
  onClose: () => void;
}> = ({ member, eid, onClose }) => {
  const [saving, setSaving] = React.useState(false);
  const toast = useToast();

  const handleActivate = async () => {
    setSaving(true);
    try {
      await membersApi.activateMember(eid, member.user.id);
      toast("Membro reativado");
      onClose();
    } catch (e: any) {
      toast(e?.message ?? "Erro ao reativar", "danger");
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async () => {
    setSaving(true);
    try {
      await membersApi.deactivateMember(eid, member.user.id);
      toast("Membro desativado");
      onClose();
    } catch (e: any) {
      toast(e?.message ?? "Erro ao desativar", "danger");
    } finally {
      setSaving(false);
    }
  };

  const handleRemove = async () => {
    if (!window.confirm(`Remover ${member.user.name} da equipe? Esta ação não pode ser desfeita.`)) return;
    setSaving(true);
    try {
      await membersApi.removeMember(eid, member.user.id);
      toast("Membro removido");
      onClose();
    } catch (e: any) {
      toast(e?.message ?? "Erro ao remover", "danger");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 18 }}>
        <Avatar name={member.user.name} size={72} />
        <div style={{ fontFamily: "var(--font-display)", fontSize: 22, marginTop: 10 }}>
          {member.user.name}
        </div>
        <div style={{ fontSize: 14, color: "var(--text-dim)", marginTop: 4 }}>{member.user.email}</div>
        {member.user.phone && (
          <div style={{ fontSize: 14, color: "var(--text-dim)" }}>{member.user.phone}</div>
        )}
      </div>

      <div style={{ display: "flex", gap: 6, justifyContent: "center", marginBottom: 22 }}>
        <Badge tone={member.role === "establishment_admin" ? "primary" : "neutral"}>
          {ROLE_LABEL[member.role] ?? member.role}
        </Badge>
        {!member.is_active && <Badge>Inativo</Badge>}
      </div>

      <div style={{ display: "flex", gap: 10 }}>
        {member.is_active ? (
          <Button variant="secondary" onClick={handleDeactivate} disabled={saving} fullWidth>
            Desativar
          </Button>
        ) : (
          <Button variant="secondary" onClick={handleActivate} disabled={saving} fullWidth>
            Reativar
          </Button>
        )}
        <Button variant="danger" onClick={handleRemove} disabled={saving} fullWidth>
          Remover
        </Button>
      </div>
    </div>
  );
};
