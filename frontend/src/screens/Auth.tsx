import * as React from "react";
import { useAuth } from "@/store/auth";
import { Icons } from "@/components/icons";
import { Button, Input } from "@/components/ui";
import { useToast } from "@/components/ToastProvider";

export const Auth: React.FC = () => {
  const { login } = useAuth();
  const toast = useToast();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [loading, setLoading] = React.useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      toast(err?.message ?? "Não foi possível entrar", "danger");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh", background: "var(--bg)", display: "flex", alignItems: "center", justifyContent: "center",
      padding: "32px 20px", paddingTop: "max(32px, env(safe-area-inset-top))",
    }}>
      <div style={{ width: "100%", maxWidth: 420 }}>
        <div style={{ textAlign: "center", marginBottom: 36 }}>
          <div style={{
            display: "inline-flex", width: 60, height: 60, borderRadius: 18,
            background: "var(--color-primary)", color: "white",
            alignItems: "center", justifyContent: "center", marginBottom: 18,
          }}>
            <Icons.sparkle size={28} />
          </div>
          <h1 style={{ margin: 0, fontFamily: "var(--font-display)", fontSize: 38, fontWeight: 400, lineHeight: 1.05, letterSpacing: "-0.02em" }}>
            Bem-vindo<br />de volta.
          </h1>
          <div style={{ color: "var(--text-dim)", marginTop: 12, fontSize: 15 }}>
            Entre no painel da <span style={{ fontWeight: 500, color: "var(--text)" }}>Agenda</span>
          </div>
        </div>

        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <Input label="E-mail ou usuário" type="text" value={email} onChange={(e) => setEmail(e.target.value)} prefix={<Icons.mail size={18} />} required />
          <Input label="Senha" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          <Button type="submit" size="lg" fullWidth disabled={loading}>{loading ? "Entrando..." : "Entrar"}</Button>
        </form>
      </div>
    </div>
  );
};
