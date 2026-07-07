import * as React from "react";
import { Icons } from "./icons";

export const Avatar: React.FC<{ name?: string; color?: string; size?: number }> = ({
  name, color, size = 36,
}) => {
  const initials = (name || "?").split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase();
  return (
    <div style={{
      width: size, height: size, borderRadius: "50%",
      background: color || "var(--color-primary)",
      color: "white", fontSize: size * 0.38, fontWeight: 600,
      display: "inline-flex", alignItems: "center", justifyContent: "center",
      flexShrink: 0, letterSpacing: "0.02em",
    }}>{initials}</div>
  );
};

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "soft";
  size?: "sm" | "md" | "lg";
  icon?: React.ReactNode;
  fullWidth?: boolean;
};

export const Button: React.FC<ButtonProps> = ({
  variant = "primary", size = "md", icon, children, fullWidth, style, ...rest
}) => {
  const sizes = {
    sm: { padding: "6px 12px", fontSize: 13, height: 32, gap: 6 },
    md: { padding: "10px 16px", fontSize: 14, height: 40, gap: 8 },
    lg: { padding: "12px 20px", fontSize: 15, height: 48, gap: 10 },
  } as const;
  const variants = {
    primary: { background: "var(--color-primary)", color: "white", border: "1px solid var(--color-primary)" },
    secondary: { background: "var(--surface)", color: "var(--text)", border: "1px solid var(--border)" },
    ghost: { background: "transparent", color: "var(--text)", border: "1px solid transparent" },
    danger: { background: "transparent", color: "#B83A3A", border: "1px solid #E5C2C2" },
    soft: { background: "var(--color-primary-soft)", color: "var(--color-primary-deep)", border: "1px solid transparent" },
  } as const;
  return (
    <button {...rest} style={{
      ...sizes[size], ...variants[variant],
      borderRadius: 999, fontWeight: 500, cursor: "pointer",
      display: "inline-flex", alignItems: "center", justifyContent: "center",
      width: fullWidth ? "100%" : undefined, fontFamily: "inherit",
      transition: "transform .08s, opacity .15s, background .15s",
      ...style,
    }}>
      {icon && <span style={{ display: "inline-flex" }}>{icon}</span>}
      {children}
    </button>
  );
};

export const IconButton: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & { icon: React.ReactNode }> = ({
  icon, style, ...rest
}) => (
  <button {...rest} style={{
    width: 38, height: 38, borderRadius: 999, border: "1px solid var(--border)",
    background: "var(--surface)", color: "var(--text)", cursor: "pointer",
    display: "inline-flex", alignItems: "center", justifyContent: "center",
    ...style,
  }}>{icon}</button>
);

type InputProps = Omit<React.InputHTMLAttributes<HTMLInputElement>, 'prefix' | 'suffix'> & {
  label?: string; error?: string; hint?: string;
  prefix?: React.ReactNode; suffix?: React.ReactNode;
};

export const Input: React.FC<InputProps> = ({ label, error, hint, prefix, suffix, style, ...rest }) => (
  <label style={{ display: "block", minWidth: 0 }}>
    {label && <div style={{ fontSize: 13, color: "var(--text-dim)", marginBottom: 6, fontWeight: 500 }}>{label}</div>}
    <div style={{
      display: "flex", alignItems: "center", gap: 8,
      background: "var(--surface)", border: `1px solid ${error ? "#D58484" : "var(--border)"}`,
      borderRadius: 12, padding: "0 14px", height: 46,
    }}>
      {prefix && <span style={{ color: "var(--text-dim)", display: "inline-flex" }}>{prefix}</span>}
      <input {...rest} style={{
        flex: 1, minWidth: 0, border: 0, outline: 0, background: "transparent",
        fontSize: 15, color: "var(--text)", fontFamily: "inherit",
        ...style,
      }} />
      {suffix}
    </div>
    {hint && !error && <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 4 }}>{hint}</div>}
    {error && <div style={{ fontSize: 12, color: "#B83A3A", marginTop: 4 }}>{error}</div>}
  </label>
);

export const Textarea: React.FC<React.TextareaHTMLAttributes<HTMLTextAreaElement> & { label?: string }> = ({
  label, rows = 3, style, ...rest
}) => (
  <label style={{ display: "block" }}>
    {label && <div style={{ fontSize: 13, color: "var(--text-dim)", marginBottom: 6, fontWeight: 500 }}>{label}</div>}
    <textarea {...rest} rows={rows} style={{
      width: "100%", border: "1px solid var(--border)", background: "var(--surface)",
      borderRadius: 12, padding: "12px 14px", fontSize: 15, color: "var(--text)",
      fontFamily: "inherit", outline: "none", resize: "vertical",
      ...style,
    }} />
  </label>
);

type SelectProps = {
  label?: string; placeholder?: string;
  options: { value: string; label: string }[];
  value: string;
  onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  disabled?: boolean;
};

export const Select: React.FC<SelectProps> = ({ label, options, value, onChange, placeholder, disabled }) => (
  <label style={{ display: "block", minWidth: 0 }}>
    {label && <div style={{ fontSize: 13, color: "var(--text-dim)", marginBottom: 6, fontWeight: 500 }}>{label}</div>}
    <div style={{ position: "relative" }}>
      <select value={value || ""} onChange={onChange} disabled={disabled} style={{
        width: "100%", minWidth: 0, appearance: "none", border: "1px solid var(--border)",
        background: "var(--surface)", borderRadius: 12, padding: "0 40px 0 14px",
        height: 46, fontSize: 15, color: "var(--text)", fontFamily: "inherit", outline: "none",
        opacity: disabled ? 0.6 : 1, cursor: disabled ? "not-allowed" : undefined,
      }}>
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
      <span style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", color: "var(--text-dim)", pointerEvents: "none" }}>
        <Icons.chevronDown size={18} />
      </span>
    </div>
  </label>
);

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement> & { padded?: boolean }> = ({
  children, padded = true, style, ...rest
}) => (
  <div {...rest} style={{
    background: "var(--surface)", border: "1px solid var(--border)",
    borderRadius: "var(--radius)", padding: padded ? "var(--card-pad)" : 0,
    ...style,
  }}>{children}</div>
);

type Tone = "neutral" | "success" | "warning" | "danger" | "info" | "primary";

export const Badge: React.FC<{ children: React.ReactNode; tone?: Tone }> = ({ children, tone = "neutral" }) => {
  const tones: Record<Tone, { bg: string; fg: string }> = {
    neutral: { bg: "var(--bg-muted)", fg: "var(--text-dim)" },
    success: { bg: "#E5F0E5", fg: "#3D6B3D" },
    warning: { bg: "#FBEFD9", fg: "#8A6017" },
    danger: { bg: "#F5DEDE", fg: "#8C2E2E" },
    info: { bg: "#DDE6F0", fg: "#3D5874" },
    primary: { bg: "var(--color-primary-soft)", fg: "var(--color-primary-deep)" },
  };
  const t = tones[tone];
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: "3px 10px", borderRadius: 999, fontSize: 12, fontWeight: 500,
      background: t.bg, color: t.fg, lineHeight: 1.4,
    }}>{children}</span>
  );
};

const STATUS_LABEL: Record<string, { label: string; tone: Tone }> = {
  pending: { label: "Pendente", tone: "warning" },
  confirmed: { label: "Confirmado", tone: "success" },
  cancelled: { label: "Cancelado", tone: "danger" },
  completed: { label: "Concluído", tone: "info" },
  sent: { label: "Enviado", tone: "success" },
  failed: { label: "Falhou", tone: "danger" },
};

export const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const s = STATUS_LABEL[status] || STATUS_LABEL.pending;
  return <Badge tone={s.tone}>{s.label}</Badge>;
};

export const Sheet: React.FC<{
  open: boolean; onClose: () => void; title?: string;
  children: React.ReactNode; footer?: React.ReactNode; size?: "sm" | "md" | "lg";
}> = ({ open, onClose, title, children, footer, size = "md" }) => {
  const [rendered, setRendered] = React.useState(open);
  const [visible, setVisible] = React.useState(false);
  const [dragY, setDragY] = React.useState(0);
  const dragRef = React.useRef({ startY: 0, isDragging: false, currentY: 0 });

  React.useEffect(() => {
    if (open) {
      setRendered(true);
      requestAnimationFrame(() => setVisible(true));
    } else {
      setVisible(false);
      const t = setTimeout(() => setRendered(false), 220);
      return () => clearTimeout(t);
    }
  }, [open]);

  React.useEffect(() => {
    const onMove = (e: TouchEvent) => {
      if (!dragRef.current.isDragging) return;
      const delta = Math.max(0, e.touches[0].clientY - dragRef.current.startY);
      dragRef.current.currentY = delta;
      setDragY(delta);
    };
    const onEnd = () => {
      if (!dragRef.current.isDragging) return;
      dragRef.current.isDragging = false;
      if (dragRef.current.currentY > 80) onClose();
      dragRef.current.currentY = 0;
      setDragY(0);
    };
    window.addEventListener("touchmove", onMove, { passive: true });
    window.addEventListener("touchend", onEnd);
    return () => {
      window.removeEventListener("touchmove", onMove);
      window.removeEventListener("touchend", onEnd);
    };
  }, [onClose]);

  if (!rendered) return null;

  const isDragging = dragY > 0;
  const backdropOpacity = visible ? Math.max(0, 1 - dragY / 300) : 0;

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 100,
      display: "flex", alignItems: "flex-end", justifyContent: "center",
    }}>
      <div onClick={onClose} style={{
        position: "absolute", inset: 0, background: "rgba(40,28,22,0.35)",
        opacity: backdropOpacity, transition: isDragging ? "none" : "opacity .22s ease",
      }} />
      <div style={{
        position: "relative", width: "100%",
        maxWidth: size === "lg" ? 720 : size === "sm" ? 420 : 560,
        background: "var(--surface)", color: "var(--text)",
        borderTopLeftRadius: 24, borderTopRightRadius: 24,
        maxHeight: "92vh", display: "flex", flexDirection: "column",
        transform: visible ? `translateY(${dragY}px)` : "translateY(100%)",
        transition: isDragging ? "none" : "transform .26s cubic-bezier(.2,.8,.2,1)",
        boxShadow: "0 -10px 40px rgba(40,28,22,.12)",
      }}>
        <div
          onTouchStart={(e) => {
            dragRef.current.startY = e.touches[0].clientY;
            dragRef.current.isDragging = true;
            dragRef.current.currentY = 0;
          }}
          style={{ display: "flex", justifyContent: "center", padding: "10px 0 0", cursor: "grab", touchAction: "none" }}
        >
          <div style={{ width: 40, height: 4, background: "var(--border)", borderRadius: 2 }} />
        </div>
        {title && (
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "12px 20px 8px", borderBottom: "1px solid var(--border)",
          }}>
            <h2 style={{ margin: 0, fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 500 }}>{title}</h2>
            <IconButton icon={<Icons.x size={18} />} onClick={onClose} style={{ width: 34, height: 34 }} />
          </div>
        )}
        <div style={{ flex: 1, overflowY: "auto", padding: 20 }}>{children}</div>
        {footer && (
          <div style={{ padding: 16, borderTop: "1px solid var(--border)", background: "var(--surface)" }}>
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

export const PageHeader: React.FC<{ title: string; subtitle?: string; action?: React.ReactNode }> = ({
  title, subtitle, action,
}) => (
  <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 16, marginBottom: 20 }}>
    <div style={{ minWidth: 0 }}>
      <h1 style={{ margin: 0, fontFamily: "var(--font-display)", fontSize: "var(--h1-size)", fontWeight: 400, lineHeight: 1.05, letterSpacing: "-0.01em" }}>{title}</h1>
      {subtitle && <div style={{ color: "var(--text-dim)", marginTop: 4, fontSize: 14 }}>{subtitle}</div>}
    </div>
    {action}
  </div>
);

export const EmptyState: React.FC<{ icon?: React.ReactNode; title: string; description?: string; action?: React.ReactNode }> = ({
  icon, title, description, action,
}) => (
  <div style={{ textAlign: "center", padding: "48px 20px", color: "var(--text-dim)" }}>
    {icon && <div style={{ display: "inline-flex", padding: 14, background: "var(--bg-muted)", borderRadius: 999, marginBottom: 14, color: "var(--color-primary)" }}>{icon}</div>}
    <div style={{ fontFamily: "var(--font-display)", fontSize: 22, color: "var(--text)", marginBottom: 6 }}>{title}</div>
    {description && <div style={{ fontSize: 14, marginBottom: 16, maxWidth: 320, marginLeft: "auto", marginRight: "auto" }}>{description}</div>}
    {action}
  </div>
);

export const FAB: React.FC<{ onClick: () => void }> = ({ onClick }) => (
  <button onClick={onClick} style={{
    position: "fixed", right: 22, bottom: "calc(var(--bottom-nav-h) + env(safe-area-inset-bottom) + 16px)",
    width: 58, height: 58, borderRadius: 999,
    background: "var(--color-primary)", color: "white", border: 0,
    boxShadow: "0 10px 24px rgba(201, 123, 92, 0.35)", cursor: "pointer", zIndex: 20,
    display: "inline-flex", alignItems: "center", justifyContent: "center",
  }}><Icons.plus size={24} /></button>
);

export const Toggle: React.FC<{ checked: boolean; onChange: (v: boolean) => void }> = ({ checked, onChange }) => (
  <button onClick={() => onChange(!checked)} style={{
    width: 42, height: 24, borderRadius: 999,
    background: checked ? "var(--color-primary)" : "var(--bg-muted)",
    border: 0, cursor: "pointer", position: "relative", transition: "background .15s",
  }}>
    <span style={{
      position: "absolute", top: 2, left: checked ? 20 : 2,
      width: 20, height: 20, borderRadius: 999, background: "white",
      transition: "left .15s", boxShadow: "0 1px 3px rgba(0,0,0,.2)",
    }} />
  </button>
);
