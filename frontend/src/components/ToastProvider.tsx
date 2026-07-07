import * as React from "react";

type Tone = "success" | "danger";
type ToastFn = (msg: string, tone?: Tone) => void;

const ToastContext = React.createContext<ToastFn | null>(null);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = React.useState<{ id: string; msg: string; tone: Tone }[]>([]);
  const push: ToastFn = React.useCallback((msg, tone = "success") => {
    const id = Math.random().toString(36).slice(2);
    setToasts((t) => [...t, { id, msg, tone }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 2800);
  }, []);
  return (
    <ToastContext.Provider value={push}>
      {children}
      <div style={{
        position: "fixed", bottom: "calc(env(safe-area-inset-bottom) + 80px)", left: 0, right: 0,
        display: "flex", flexDirection: "column", alignItems: "center", gap: 8, zIndex: 200,
        pointerEvents: "none",
      }}>
        {toasts.map((t) => (
          <div key={t.id} style={{
            background: t.tone === "danger" ? "#5C2828" : "var(--text)", color: "var(--bg)",
            padding: "10px 18px", borderRadius: 999, fontSize: 14, fontWeight: 500,
            boxShadow: "0 8px 24px rgba(0,0,0,.18)", animation: "toastIn .25s ease",
          }}>{t.msg}</div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastFn => {
  const ctx = React.useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside ToastProvider");
  return ctx;
};
