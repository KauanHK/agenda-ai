import * as React from "react";
import { NavLink } from "react-router-dom";
import { Icons, type IconName } from "./icons";
import { Avatar } from "./ui";
import { useAuth } from "@/store/auth";
import { useTheme } from "@/lib/theme";

const NAV_PRIMARY: { to: string; label: string; icon: IconName }[] = [
  { to: "/", label: "Hoje", icon: "home" },
  { to: "/calendar", label: "Calendário", icon: "calendar" },
  { to: "/appointments", label: "Agenda", icon: "list" },
  { to: "/clients", label: "Clientes", icon: "users" },
];

const NAV_SECONDARY: { to: string; label: string; icon: IconName }[] = [
  { to: "/services", label: "Serviços", icon: "scissors" },
  { to: "/hours", label: "Horários", icon: "clock" },
  { to: "/templates", label: "Templates", icon: "message" },
  { to: "/notifications", label: "Notificações", icon: "bell" },
  { to: "/team", label: "Equipe", icon: "user" },
  { to: "/settings", label: "Configurações", icon: "settings" },
];

const NAV_ALL = [...NAV_PRIMARY, ...NAV_SECONDARY];

const themeButtonStyle: React.CSSProperties = {
  background: "transparent", border: 0, cursor: "pointer",
  color: "var(--text-dim)", display: "flex", alignItems: "center", justifyContent: "center",
  padding: 8, borderRadius: 8,
};

export const Shell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isDesktop, setIsDesktop] = React.useState(() => window.matchMedia("(min-width: 900px)").matches);
  const [moreOpen, setMoreOpen] = React.useState(false);
  const [estMenuOpen, setEstMenuOpen] = React.useState(false);
  const { user, activeEstablishment, establishments, switchEstablishment, logout } = useAuth();
  const { theme, toggle } = useTheme();

  React.useEffect(() => {
    const mq = window.matchMedia("(min-width: 900px)");
    const h = (e: MediaQueryListEvent) => setIsDesktop(e.matches);
    mq.addEventListener("change", h);
    return () => mq.removeEventListener("change", h);
  }, []);

  const sectionTitle = NAV_ALL.find((n) => n.to === window.location.pathname)?.label || "";
  const estName = activeEstablishment?.name ?? "Agenda";

  const EstSwitcher = () => establishments.length <= 1 ? null : (
    <div style={{ position: "relative" }}>
      <button onClick={() => setEstMenuOpen((v) => !v)} style={{
        background: "var(--bg-muted)", border: "1px solid var(--border)", borderRadius: 8,
        padding: "4px 8px", fontSize: 11, cursor: "pointer", fontFamily: "inherit", color: "var(--text-dim)",
      }}>Trocar ▾</button>
      {estMenuOpen && (
        <div style={{ position: "absolute", top: "100%", left: 0, marginTop: 4, background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 10, padding: 4, minWidth: 200, zIndex: 50, boxShadow: "0 8px 24px rgba(0,0,0,0.08)" }}>
          {establishments.map((e) => (
            <button key={e.id} onClick={() => { switchEstablishment(e.id); setEstMenuOpen(false); }} style={{
              display: "block", width: "100%", textAlign: "left", padding: "8px 10px", background: e.id === activeEstablishment?.id ? "var(--color-primary-soft)" : "transparent",
              border: 0, borderRadius: 6, fontSize: 13, fontFamily: "inherit", cursor: "pointer", color: "inherit",
            }}>{e.name}</button>
          ))}
        </div>
      )}
    </div>
  );

  if (isDesktop) {
    return (
      <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg)" }}>
        <aside style={{
          width: 240, background: "var(--surface)", borderRight: "1px solid var(--border)",
          display: "flex", flexDirection: "column", position: "sticky", top: 0, height: "100vh",
        }}>
          <div style={{ padding: "22px 22px 16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{
                width: 34, height: 34, borderRadius: 10,
                background: "var(--color-primary)", color: "white",
                display: "inline-flex", alignItems: "center", justifyContent: "center",
              }}><Icons.sparkle size={18} /></div>
              <div style={{ minWidth: 0, flex: 1 }}>
                <div style={{ fontFamily: "var(--font-display)", fontSize: 18, lineHeight: 1.05, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{estName}</div>
                <div style={{ fontSize: 11, color: "var(--text-dim)", display: "flex", alignItems: "center", gap: 6 }}>
                  painel <EstSwitcher />
                </div>
              </div>
            </div>
          </div>
          <nav style={{ padding: "8px 12px", flex: 1, overflowY: "auto" }}>
            {NAV_ALL.map((n) => {
              const Ic = Icons[n.icon];
              return (
                <NavLink key={n.to} to={n.to} end={n.to === "/"} style={({ isActive }) => ({
                  display: "flex", alignItems: "center", gap: 12, width: "100%",
                  padding: "10px 12px", borderRadius: 10, marginBottom: 2,
                  background: isActive ? "var(--color-primary-soft)" : "transparent",
                  color: isActive ? "var(--color-primary-deep)" : "var(--text)",
                  textDecoration: "none", fontSize: 14,
                  fontWeight: isActive ? 600 : 400,
                })}>
                  <Ic size={18} /> {n.label}
                </NavLink>
              );
            })}
          </nav>
          <div style={{ padding: 14, borderTop: "1px solid var(--border)" }}>
            {user && <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 8, padding: "0 12px" }}>{user.name}</div>}
            <div style={{ display: "flex", alignItems: "center" }}>
              <button onClick={logout} style={{
                display: "flex", alignItems: "center", gap: 10, flex: 1,
                padding: "10px 12px", borderRadius: 10, background: "transparent",
                color: "var(--text-dim)", border: 0, cursor: "pointer", fontSize: 13, fontFamily: "inherit",
              }}><Icons.logout size={16} />Sair</button>
              <button onClick={toggle} style={themeButtonStyle} title={theme === "dark" ? "Modo claro" : "Modo escuro"}>
                {theme === "dark" ? <Icons.sun size={18} /> : <Icons.moon size={18} />}
              </button>
            </div>
          </div>
        </aside>
        <main style={{ flex: 1, minWidth: 0 }}>{children}</main>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", paddingBottom: "calc(var(--bottom-nav-h) + env(safe-area-inset-bottom))" }}>
      <header style={{
        position: "sticky", top: 0, zIndex: 30,
        background: "var(--bg)", borderBottom: "1px solid var(--border)",
        padding: "12px 18px", display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div>
          <div style={{ fontSize: 11, color: "var(--text-dim)", letterSpacing: "0.05em", textTransform: "uppercase" }}>{estName}</div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 22, lineHeight: 1.05, marginTop: 2 }}>{sectionTitle}</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <button onClick={toggle} style={themeButtonStyle} title={theme === "dark" ? "Modo claro" : "Modo escuro"}>
            {theme === "dark" ? <Icons.sun size={20} /> : <Icons.moon size={20} />}
          </button>
          {user && <Avatar name={user.name} size={36} />}
        </div>
      </header>

      <div>{children}</div>

      <nav style={{
        position: "fixed", bottom: 0, left: 0, right: 0,
        background: "var(--surface)", borderTop: "1px solid var(--border)",
        height: "var(--bottom-nav-h)", paddingBottom: "env(safe-area-inset-bottom)",
        display: "flex", zIndex: 40,
      }}>
        {NAV_PRIMARY.map((n) => {
          const Ic = Icons[n.icon];
          return (
            <NavLink key={n.to} to={n.to} end={n.to === "/"} style={({ isActive }) => ({
              flex: 1, background: "transparent", border: 0, cursor: "pointer",
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 3,
              color: isActive ? "var(--color-primary)" : "var(--text-dim)",
              fontSize: 11, fontFamily: "inherit", paddingTop: 6, textDecoration: "none",
              fontWeight: isActive ? 600 : 400,
            })}>
              <Ic size={22} /> <span>{n.label}</span>
            </NavLink>
          );
        })}
        <button onClick={() => setMoreOpen(true)} style={{
          flex: 1, background: "transparent", border: 0, cursor: "pointer",
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 3,
          color: "var(--text-dim)", fontSize: 11, fontFamily: "inherit", paddingTop: 6,
        }}>
          <Icons.menu size={22} /> <span>Mais</span>
        </button>
      </nav>

      {moreOpen && (
        <div style={{ position: "fixed", inset: 0, zIndex: 80, display: "flex", alignItems: "flex-end" }}>
          <div onClick={() => setMoreOpen(false)} style={{ position: "absolute", inset: 0, background: "rgba(40,28,22,0.4)" }} />
          <div style={{
            position: "relative", width: "100%",
            background: "var(--surface)", borderTopLeftRadius: 24, borderTopRightRadius: 24,
            padding: 16, paddingBottom: "calc(env(safe-area-inset-bottom) + 16px)",
          }}>
            <div style={{ display: "flex", justifyContent: "center", marginBottom: 12 }}>
              <div style={{ width: 40, height: 4, background: "var(--border)", borderRadius: 2 }} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
              {NAV_SECONDARY.map((n) => {
                const Ic = Icons[n.icon];
                return (
                  <NavLink key={n.to} to={n.to} onClick={() => setMoreOpen(false)} style={{
                    display: "flex", flexDirection: "column", alignItems: "center", gap: 6,
                    padding: "14px 10px", borderRadius: 14, background: "var(--bg-muted)",
                    color: "var(--text)", textDecoration: "none", fontSize: 12,
                  }}>
                    <Ic size={22} /> {n.label}
                  </NavLink>
                );
              })}
              <button onClick={() => { logout(); setMoreOpen(false); }} style={{
                display: "flex", flexDirection: "column", alignItems: "center", gap: 6,
                padding: "14px 10px", borderRadius: 14, background: "var(--bg-muted)",
                color: "var(--text-dim)", border: 0, cursor: "pointer", fontFamily: "inherit", fontSize: 12,
              }}><Icons.logout size={22} />Sair</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
