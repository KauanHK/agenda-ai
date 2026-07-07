// Sidebar shell used by all /admin/* routes.
//
// Renders only when the logged-in user has is_global_admin = true.
// Distinct from the regular Shell so the visual context makes it
// obvious you are operating "above" any one establishment.
//
// Provides:
//   • dedicated nav (Estabelecimentos, Usuários)
//   • a "Modo admin global" header strip
//   • a "voltar à operação" link for admins who also belong to
//     at least one establishment

import * as React from "react";
import { NavLink, useLocation } from "react-router-dom";
import { Icons } from "@/components/icons";
import { useAuth } from "@/store/auth";

const NAV: { to: string; label: string; icon: keyof typeof Icons }[] = [
  { to: "/admin/establishments", label: "Estabelecimentos", icon: "home" },
  { to: "/admin/users", label: "Usuários", icon: "users" },
];

export const AdminShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isDesktop, setIsDesktop] = React.useState(() => window.matchMedia("(min-width: 900px)").matches);
  const { user, establishments, logout } = useAuth();
  const hasEstablishments = establishments.length > 0;
  const location = useLocation();

  React.useEffect(() => {
    const mq = window.matchMedia("(min-width: 900px)");
    const h = (e: MediaQueryListEvent) => setIsDesktop(e.matches);
    mq.addEventListener("change", h);
    return () => mq.removeEventListener("change", h);
  }, []);

  const sectionTitle = NAV.find((n) => location.pathname.startsWith(n.to))?.label ?? "Admin global";

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
                background: "var(--text)", color: "var(--surface)",
                display: "inline-flex", alignItems: "center", justifyContent: "center",
              }}>
                <Icons.settings size={18} />
              </div>
              <div style={{ minWidth: 0, flex: 1 }}>
                <div style={{ fontFamily: "var(--font-display)", fontSize: 18, lineHeight: 1.05 }}>Admin global</div>
                <div style={{ fontSize: 11, color: "var(--text-dim)" }}>painel da plataforma</div>
              </div>
            </div>
          </div>

          <nav style={{ padding: "8px 12px", flex: 1, overflowY: "auto" }}>
            {NAV.map((n) => {
              const Ic = Icons[n.icon];
              return (
                <NavLink key={n.to} to={n.to} style={({ isActive }) => ({
                  display: "flex", alignItems: "center", gap: 12, width: "100%",
                  padding: "10px 12px", borderRadius: 10, marginBottom: 2,
                  background: isActive ? "var(--bg-muted)" : "transparent",
                  color: isActive ? "var(--text)" : "var(--text-dim)",
                  textDecoration: "none", fontSize: 14,
                  fontWeight: isActive ? 600 : 400,
                })}>
                  <Ic size={18} /> {n.label}
                </NavLink>
              );
            })}
          </nav>

          <div style={{ padding: 14, borderTop: "1px solid var(--border)", display: "flex", flexDirection: "column", gap: 4 }}>
            {hasEstablishments && (
              <NavLink to="/" style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "10px 12px", borderRadius: 10,
                color: "var(--text-dim)", textDecoration: "none", fontSize: 13,
              }}>
                <Icons.chevronLeft size={16} /> Voltar à operação
              </NavLink>
            )}
            {user && <div style={{ fontSize: 12, color: "var(--text-dim)", padding: "4px 12px" }}>{user.name}</div>}
            <button onClick={logout} style={{
              display: "flex", alignItems: "center", gap: 10, width: "100%",
              padding: "10px 12px", borderRadius: 10, background: "transparent",
              color: "var(--text-dim)", border: 0, cursor: "pointer", fontSize: 13, fontFamily: "inherit",
            }}><Icons.logout size={16} />Sair</button>
          </div>
        </aside>

        <main style={{ flex: 1, minWidth: 0 }}>
          <AdminBanner />
          {children}
        </main>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <AdminBanner />
      <header style={{
        position: "sticky", top: 0, zIndex: 30,
        background: "var(--bg)", borderBottom: "1px solid var(--border)",
        padding: "12px 18px", display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div>
          <div style={{ fontSize: 11, color: "var(--text-dim)", letterSpacing: "0.05em", textTransform: "uppercase" }}>
            Admin global
          </div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 22, lineHeight: 1.05, marginTop: 2 }}>{sectionTitle}</div>
        </div>
        {hasEstablishments && (
          <NavLink to="/" style={{ fontSize: 12, color: "var(--text-dim)", textDecoration: "none" }}>Operação ›</NavLink>
        )}
      </header>

      <div>{children}</div>

      <nav style={{
        position: "fixed", bottom: 0, left: 0, right: 0,
        background: "var(--surface)", borderTop: "1px solid var(--border)",
        height: "var(--bottom-nav-h)", paddingBottom: "env(safe-area-inset-bottom)",
        display: "flex", zIndex: 40,
      }}>
        {NAV.map((n) => {
          const Ic = Icons[n.icon];
          return (
            <NavLink key={n.to} to={n.to} style={({ isActive }) => ({
              flex: 1, background: "transparent", border: 0, cursor: "pointer",
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 3,
              color: isActive ? "var(--text)" : "var(--text-dim)",
              fontSize: 11, fontFamily: "inherit", paddingTop: 6, textDecoration: "none",
              fontWeight: isActive ? 600 : 400,
            })}>
              <Ic size={22} /> <span>{n.label}</span>
            </NavLink>
          );
        })}
        <button onClick={logout} style={{
          flex: 1, background: "transparent", border: 0, cursor: "pointer",
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 3,
          color: "var(--text-dim)", fontSize: 11, fontFamily: "inherit", paddingTop: 6,
        }}><Icons.logout size={22} /> <span>Sair</span></button>
      </nav>

      <div style={{ height: "calc(var(--bottom-nav-h) + env(safe-area-inset-bottom))" }} />
    </div>
  );
};

const AdminBanner: React.FC = () => (
  <div style={{
    background: "var(--text)", color: "var(--surface)",
    fontSize: 12, padding: "6px 18px", textAlign: "center",
    letterSpacing: "0.04em",
  }}>
    Você está no modo administrador global da plataforma.
  </div>
);
