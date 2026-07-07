import type {
  Client, Establishment, GoogleIntegration, Notification, OperatingHour,
  Scheduling, Service, Template, User,
} from "./types";

// Mock data was removed. All collections start empty and the singleton
// objects below are neutral placeholders so the existing screens still
// compile until they are migrated to the real API.

export const establishment: Establishment = {
  id: "",
  name: "",
  cnpj: "",
  timezone: "America/Sao_Paulo",
  phone: "",
  is_active: true,
};

export const currentUser = {
  id: "",
  name: "",
  email: "",
  role: "establishment_admin" as const,
  avatar_color: "#999999",
};

export const team: User[] = [];

export const services: Service[] = [];

export const clients: Client[] = [];

export const schedulings: Scheduling[] = [];

export const operatingHours: OperatingHour[] = [
  { weekday: 0, open_time: "", close_time: "", is_open: false },
  { weekday: 1, open_time: "", close_time: "", is_open: false },
  { weekday: 2, open_time: "", close_time: "", is_open: false },
  { weekday: 3, open_time: "", close_time: "", is_open: false },
  { weekday: 4, open_time: "", close_time: "", is_open: false },
  { weekday: 5, open_time: "", close_time: "", is_open: false },
  { weekday: 6, open_time: "", close_time: "", is_open: false },
];

export const templates: Template[] = [];

export const notifications: Notification[] = [];

export const googleIntegration: GoogleIntegration = {
  connected: false,
  google_account_email: "",
  google_calendar_id: "",
  last_sync_at: "",
  scope: "",
};
