import * as React from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { Shell } from "@/components/Shell";
import { Sheet } from "@/components/ui";
import { ToastProvider } from "@/components/ToastProvider";
import { AuthProvider, useAuth } from "@/store/auth";
import { Auth } from "@/screens/Auth";
import { Dashboard } from "@/screens/Dashboard";
import { WeekCalendar } from "@/screens/Calendar";
import { AppointmentsList } from "@/screens/AppointmentsList";
import { AppointmentForm, type AppointmentFormInitial } from "@/screens/AppointmentForm";
import { AppointmentDetail } from "@/screens/AppointmentDetail";
import { Clients } from "@/screens/Clients";
import { Services } from "@/screens/Services";
import { OperatingHours } from "@/screens/OperatingHours";
import { Templates } from "@/screens/Templates";
import { Notifications } from "@/screens/Notifications";
import { Team } from "@/screens/Team";
import { Settings } from "@/screens/Settings";

const LoadingScreen: React.FC = () => (
  <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", color: "var(--text-dim)" }}>
    Carregando…
  </div>
);

const NoEstablishment: React.FC = () => {
  const { logout, user } = useAuth();
  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: 32, textAlign: "center" }}>
      <div style={{ maxWidth: 420 }}>
        <h2 style={{ marginTop: 0 }}>Sem estabelecimento</h2>
        <p style={{ color: "var(--text-dim)" }}>
          A conta {user?.email} não está vinculada a nenhum estabelecimento.
          Peça ao administrador para te adicionar como membro.
        </p>
        <button onClick={logout} style={{ marginTop: 16, background: "transparent", border: "1px solid var(--border)", padding: "10px 16px", borderRadius: 10, cursor: "pointer" }}>Sair</button>
      </div>
    </div>
  );
};

const AppShell: React.FC = () => {
  const [formOpen, setFormOpen] = React.useState(false);
  const [formInitial, setFormInitial] = React.useState<AppointmentFormInitial>({});
  const [detailId, setDetailId] = React.useState<string | null>(null);
  const [calendarRefreshKey, setCalendarRefreshKey] = React.useState(0);
  const [schedulingsVersion, setSchedulingsVersion] = React.useState(0);

  const bumpCalendar = () => setCalendarRefreshKey((k) => k + 1);
  const openEdit = (item: any) => { setDetailId(null); setFormInitial(item); setFormOpen(true); };
  const refreshSchedulings = () => setSchedulingsVersion((v) => v + 1);

  const openCreate = (date?: Date, hour?: number | null) => {
    setFormInitial({ prefillDate: date, prefillHour: hour });
    setFormOpen(true);
  };

  const closeDetail = () => { setDetailId(null); bumpCalendar(); };

  return (
    <Shell>
      <Routes>
        <Route path="/" element={<Dashboard onCreate={() => openCreate()} onOpenAppointment={setDetailId} />} />
        <Route path="/calendar" element={<WeekCalendar onCreate={openCreate} onOpenAppointment={setDetailId} refreshKey={calendarRefreshKey} />} />
        <Route path="/appointments" element={<AppointmentsList onCreate={() => openCreate()} onOpenAppointment={setDetailId} refreshKey={schedulingsVersion} />} />
        <Route path="/clients" element={<Clients />} />
        <Route path="/services" element={<Services />} />
        <Route path="/hours" element={<OperatingHours />} />
        <Route path="/templates" element={<Templates />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/team" element={<Team />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      <Sheet open={formOpen} onClose={() => setFormOpen(false)} title={formInitial?.id ? "Editar agendamento" : "Novo agendamento"} size="md">
        {formOpen && <AppointmentForm initial={formInitial} onClose={() => setFormOpen(false)} onCreated={bumpCalendar} />}
      </Sheet>

      <Sheet open={!!detailId} onClose={closeDetail} title="Detalhes">
        {detailId && <AppointmentDetail id={detailId} onEdit={openEdit} onClose={closeDetail} onSuccess={refreshSchedulings} />}
      </Sheet>
    </Shell>
  );
};

const AuthGate: React.FC = () => {
  const { status, activeEstablishment } = useAuth();
  const location = useLocation();

  if (status === "loading") return <LoadingScreen />;
  if (status === "anonymous") {
    return location.pathname === "/login"
      ? <Auth />
      : <Navigate to="/login" replace state={{ from: location }} />;
  }
  // authenticated
  if (location.pathname === "/login") return <Navigate to="/" replace />;
  if (!activeEstablishment) return <NoEstablishment />;
  return <AppShell />;
};

export const App: React.FC = () => (
  <ToastProvider>
    <AuthProvider>
      <BrowserRouter>
        <AuthGate />
      </BrowserRouter>
    </AuthProvider>
  </ToastProvider>
);
