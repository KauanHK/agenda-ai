export type Role = "global_admin" | "establishment_admin" | "member";

export type SchedulingStatus = "pending" | "confirmed" | "cancelled" | "completed";
export type SchedulingSource = "manual" | "online";
export type CancelledByType = "user" | "client" | "establishment";
export type NotificationStatus = "pending" | "sent" | "failed";

export interface Establishment {
  id: string;
  name: string;
  cnpj: string;
  timezone: string;
  phone: string;
  is_active: boolean;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  is_active: boolean;
  color: string;
  avatar_color?: string;
}

export interface Service {
  id: string;
  name: string;
  description: string;
  duration_minutes: number;
  price: number;
  is_active: boolean;
}

export interface Client {
  id: string;
  name: string;
  phone: string;
  email: string;
  is_active: boolean;
  last_visit: string | null;
}

export interface UserRef {
  id: string;
  name: string;
}

export interface ClientRef {
  id: string;
  name: string;
  phone: string;
}

export interface ServiceRef {
  id: string;
  name: string;
  duration_minutes: number;
}

export interface Scheduling {
  id: string;
  status: SchedulingStatus;
  source: SchedulingSource;
  starts_at: string;
  ends_at: string;
  cancelled_by_type: CancelledByType | null;
  cancelled_by_user_id: string | null;
  client: ClientRef;
  service: ServiceRef;
  user: UserRef;
}

export interface OperatingHour {
  weekday: number;
  open_time: string;
  close_time: string;
  is_open: boolean;
}

export interface Template {
  id: string;
  name: string;
  body: string;
  service_id: string | null;
  is_active: boolean;
}

export interface Notification {
  id: string;
  scheduling_id: string;
  template_id: string;
  send_at: string;
  status: NotificationStatus;
  sent_at: string | null;
  error_message: string;
}

export interface GoogleIntegration {
  connected: boolean;
  google_account_email: string;
  google_calendar_id: string;
  last_sync_at: string;
  scope: string;
}
