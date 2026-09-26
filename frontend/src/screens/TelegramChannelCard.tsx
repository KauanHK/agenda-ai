import * as React from "react";
import { Icons } from "@/components/icons";
import { Badge, Button, Card, Input } from "@/components/ui";
import { useToast } from "@/components/ToastProvider";
import { ApiError } from "@/api/client";
import * as channelsApi from "@/api/channels";
import type { TelegramChannelRead, UUID } from "@/api/types";
import { fmtDate } from "@/lib/date";

// O ApiError lê `detail`, mas as AppError do backend respondem com `message`:
// por isso a mensagem sai do status.
const ERROR_BY_STATUS: Record<number, string> = {
  422: "Token inválido. Confira o token com o @BotFather.",
  409: "Este bot já está conectado a outro estabelecimento.",
  502: "O Telegram não respondeu. Tente novamente em instantes.",
};

const errorMessage = (e: unknown, fallback: string) =>
  (e instanceof ApiError && ERROR_BY_STATUS[e.status]) || fallback;

interface Props {
  establishmentId: UUID;
  canEdit: boolean;
}

export const TelegramChannelCard: React.FC<Props> = ({ establishmentId, canEdit }) => {
  const toast = useToast();
  const [channel, setChannel] = React.useState<TelegramChannelRead | null>(null);
  const [editing, setEditing] = React.useState(false);
  const [token, setToken] = React.useState("");
  const [saving, setSaving] = React.useState(false);

  React.useEffect(() => {
    let cancelled = false;
    setChannel(null);
    setEditing(false);
    setToken("");
    channelsApi
      .getTelegramChannel(establishmentId)
      .then((c) => { if (!cancelled) setChannel(c); })
      .catch(() => { if (!cancelled) toast("Erro ao carregar o status do Telegram", "danger"); });
    return () => { cancelled = true; };
  }, [establishmentId, toast]);

  const connect = async () => {
    if (!token.trim()) return;
    setSaving(true);
    try {
      setChannel(await channelsApi.connectTelegram(establishmentId, token.trim()));
      setEditing(false);
      toast("Bot do Telegram conectado", "success");
    } catch (e) {
      toast(errorMessage(e, "Erro ao conectar o bot"), "danger");
    } finally {
      setToken("");
      setSaving(false);
    }
  };

  const disconnect = async () => {
    if (!window.confirm("Desconectar o bot do Telegram? Ele para de responder aos clientes.")) return;
    setSaving(true);
    try {
      await channelsApi.disconnectTelegram(establishmentId);
      setChannel({ connected: false, bot_id: null, bot_username: null, connected_at: null });
      setEditing(false);
      toast("Bot do Telegram desconectado", "success");
    } catch (e) {
      toast(errorMessage(e, "Erro ao desconectar o bot"), "danger");
    } finally {
      setSaving(false);
    }
  };

  const tokenForm = (
    <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 12 }}>
      <Input
        label="Token do bot"
        type="password"
        autoComplete="off"
        value={token}
        onChange={(e) => setToken(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter") connect(); }}
        placeholder="123456789:AA…"
      />
      <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
        {channel?.connected && (
          <Button variant="secondary" onClick={() => { setEditing(false); setToken(""); }} disabled={saving}>
            Cancelar
          </Button>
        )}
        <Button onClick={connect} disabled={saving || !token.trim()}>
          {saving ? "Conectando…" : "Conectar"}
        </Button>
      </div>
    </div>
  );

  return (
    <Card style={{ marginBottom: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 18, display: "flex", alignItems: "center", gap: 8 }}>
            <Icons.send size={20} />
            Telegram
          </div>
          <div style={{ fontSize: 13, color: "var(--text-dim)", marginTop: 2 }}>
            Atenda e agende pelo bot do Telegram do estabelecimento
          </div>
        </div>
        {channel?.connected && <Badge tone="success">Conectado</Badge>}
      </div>

      {channel === null ? (
        <div style={{ marginTop: 12, fontSize: 13, color: "var(--text-dim)" }}>Carregando…</div>
      ) : channel.connected ? (
        <>
          <div style={{ marginTop: 12, fontSize: 14 }}>
            <a href={`https://t.me/${channel.bot_username}`} target="_blank" rel="noreferrer">
              @{channel.bot_username}
            </a>
            {channel.connected_at && (
              <span style={{ color: "var(--text-dim)" }}> · desde {fmtDate(channel.connected_at)}</span>
            )}
          </div>
          {canEdit && (editing ? tokenForm : (
            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 12 }}>
              <Button variant="secondary" onClick={() => setEditing(true)} disabled={saving}>
                Trocar token
              </Button>
              <Button variant="danger" onClick={disconnect} disabled={saving}>
                Desconectar
              </Button>
            </div>
          ))}
        </>
      ) : (
        <div style={{
          marginTop: 12, padding: "12px 14px",
          background: "var(--bg-muted)", borderRadius: 12,
          fontSize: 13, color: "var(--text-dim)",
        }}>
          {canEdit ? (
            <>
              <div>1. Crie um bot no @BotFather (<code>/newbot</code>).</div>
              <div>2. Copie o token.</div>
              <div>3. Cole aqui.</div>
              {tokenForm}
            </>
          ) : (
            "Nenhum bot conectado."
          )}
        </div>
      )}
    </Card>
  );
};
