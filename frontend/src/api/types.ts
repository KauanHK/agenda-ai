// Types generated from AgendaBot OpenAPI 3.1.0
// Hand-written, but mirrors the schemas in the spec.

export type UUID = string;
export type ISODateTime = string;

export type UserRole = "establishment_admin" | "member";
export type DocumentType = "cpf" | "cnpj";
export type SchedulingStatus = "pending" | "confirmed" | "cancelled" | "completed";
export type SchedulingSource = "manual" | "online";
export type CancelledByType = "client" | "establishment" | "system";
export type ChangedBySource = "user" | "client" | "system";
export type NotificationStatus = "pending" | "sent" | "cancelled" | "failed";
export type TemplateType = "confirmation" | "reminder" | "cancellation";

export interface Paginated<T> {
  data: T[];
  total: number;
  page: number;
  size: number;
  total_pages: number;
}

export interface PageQuery {
  [key: string]: string | number | boolean | null | undefined;
  page?: number;
  size?: number;
}

// ============ Auth ============
export interface LoginRequest { username: string; password: string; }
export interface RefreshRequest { refresh_token: string; }
export interface TokenResponse { access_token: string; refresh_token: string; token_type?: string; }

// ============ Users ============
export interface UserRead {
  id: UUID;
  name: string;
  email: string;
  phone: string | null;
  is_global_admin: boolean;
  is_active: boolean;
  deleted_at: ISODateTime | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}
export interface UserCreate { name: string; email: string; phone?: string | null; password: string; role: UserRole; establishment_id?: UUID | null; }
export interface UserUpdate { name?: string | null; email?: string | null; phone?: string | null; }

// ============ Establishments ============
export interface EstablishmentRead {
  id: UUID;
  name: string;
  document: string;
  document_type: DocumentType;
  timezone: string;
  street: string;
  number: string;
  complement: string;
  neighborhood: string;
  city: string;
  state: string;
  zip_code: string;
  is_active: boolean;
  deleted_at: ISODateTime | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}
export interface EstablishmentCreate {
  name: string; document: string; document_type: DocumentType; timezone: string;
  street: string; number: string; complement: string; neighborhood: string;
  city: string; state: string; zip_code: string;
}
export type EstablishmentUpdate = Partial<Omit<EstablishmentCreate, "document_type">>;

// ============ Memberships ============
export interface MemberUserRef {
  id: UUID;
  name: string;
  email: string;
  phone: string | null;
  is_active: boolean;
}

export interface MembershipRead {
  id: UUID;
  user_id: UUID;
  establishment_id: UUID;
  role: UserRole;
  is_active: boolean;
}

export interface MembershipWithUser {
  id: UUID;
  user: MemberUserRef;
  establishment_id: UUID;
  role: UserRole;
  is_active: boolean;
}

export interface MembershipReadExpanded {
  id: UUID;
  role: UserRole;
  is_active: boolean;
  establishment_id: UUID;
  user: MemberUserRef;
  establishment: EstablishmentRead;
}

export interface MembershipCreateBody { user_id: UUID; role: UserRole; }
export interface MembershipUpdate { role: UserRole; }

// ============ Operating Hours ============
export interface OperatingHourRead { id: UUID; establishment_id: UUID; weekday: number; start_time: string; end_time: string; }
export interface OperatingHourItem { weekday: number; start_time: string; end_time: string; }
export interface OperatingHoursUpdate { items: OperatingHourItem[]; }

// ============ Channels ============
export interface TelegramChannelRead {
  connected: boolean;
  bot_id: number | null;
  bot_username: string | null;
  connected_at: ISODateTime | null;
}

// ============ Clients ============
export interface ClientRead {
  id: UUID; establishment_id: UUID;
  name: string; phone: string; email: string | null;
  is_active: boolean;
  created_at: ISODateTime; updated_at: ISODateTime;
}
export interface ClientCreate { name: string; phone: string; email?: string | null; }
export interface ClientUpdate { name?: string | null; phone?: string | null; email?: string | null; is_active?: boolean | null; }

// ============ Services ============
export interface ServiceRead {
  id: UUID; establishment_id: UUID;
  name: string; description: string | null;
  duration_minutes: number; price: string;
  is_active: boolean;
  created_at: ISODateTime; updated_at: ISODateTime;
}
export interface ServiceCreate { name: string; description?: string | null; duration_minutes: number; price: number | string; }
export interface ServiceUpdate {
  name?: string | null; description?: string | null;
  duration_minutes?: number | null; price?: number | string | null;
  is_active?: boolean | null;
}

// ============ Schedulings ============
export interface UserRef { id: UUID; name: string; }
export interface ClientRef { id: UUID; name: string; phone: string; }
export interface ServiceRef { id: UUID; name: string; duration_minutes: number; }

export interface SchedulingRead {
  id: UUID; establishment_id: UUID;
  status: SchedulingStatus; source: SchedulingSource;
  starts_at: ISODateTime; ends_at: ISODateTime;
  cancelled_by_type: CancelledByType | null;
  cancelled_by_user_id: UUID | null;
  created_at: ISODateTime; updated_at: ISODateTime;
  client: ClientRef; service: ServiceRef; user: UserRef;
}
export type SchedulingExpandedRead = SchedulingRead;
export interface SchedulingCreate { user_id: UUID; client_id: UUID; service_id: UUID; starts_at: ISODateTime; }
export interface SchedulingUpdate { user_id?: UUID; client_id?: UUID; service_id?: UUID; starts_at?: ISODateTime; }
export interface CancelSchedulingRequest { cancelled_by_type: CancelledByType; cancelled_by_user_id?: UUID | null; }
export interface RescheduleRequest { starts_at: ISODateTime; }

export interface SchedulingStatusLogRead {
  id: UUID; scheduling_id: UUID;
  from_status: SchedulingStatus | null; to_status: SchedulingStatus;
  changed_by_source: ChangedBySource; changed_by_user_id: UUID | null;
  note: string | null; changed_at: ISODateTime;
}

// ============ Messaging Templates ============
export interface TemplateServiceRef { id: UUID; name: string; }

export interface MessagingTemplateRead {
  id: UUID; establishment_id: UUID;
  name: string; content: string;
  type: TemplateType;
  minutes_before: number | null;
  is_active: boolean;
  created_at: ISODateTime; updated_at: ISODateTime;
  services?: TemplateServiceRef[];
}
export interface MessagingTemplateCreate {
  name: string; content: string; type: TemplateType;
  minutes_before?: number | null;
}
export interface MessagingTemplateUpdate {
  name?: string | null; content?: string | null;
  type?: TemplateType | null; minutes_before?: number | null;
  is_active?: boolean | null;
}

// ============ Scheduling Notifications ============
export interface SchedulingNotificationRead {
  id: UUID; establishment_id: UUID;
  scheduling_id: UUID; template_id: UUID | null;
  scheduled_at: ISODateTime;
  status: NotificationStatus;
  content_at_send: string | null;
  sent_at: ISODateTime | null;
  attempts: number;
  last_attempt_at: ISODateTime | null;
  last_error: string | null;
  created_at: ISODateTime; updated_at: ISODateTime;
}

// ============ Dashboard ============
export interface DashboardAgendaItem {
  id: UUID;
  establishment_id: UUID;
  status: SchedulingStatus;
  source: SchedulingSource;
  starts_at: ISODateTime;
  ends_at: ISODateTime;
  cancelled_by_type: CancelledByType | null;
  cancelled_by_user_id: UUID | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
  client: ClientRef;
  service: ServiceRef;
  user: UserRef;
}

export interface DashboardResponse {
  today_total: number;
  today_confirmed: number;
  pending_count: number;
  expected_revenue: string;
  agenda: DashboardAgendaItem[];
}

// ============ Unavailabilities ============
export interface UnavailabilityRead {
  id: UUID; establishment_id: UUID;
  starts_at: ISODateTime; ends_at: ISODateTime;
  reason: string | null;
  created_at: ISODateTime; updated_at: ISODateTime;
}
export interface UnavailabilityCreate { starts_at: ISODateTime; ends_at: ISODateTime; reason?: string | null; }
export interface UnavailabilityUpdate { starts_at?: ISODateTime | null; ends_at?: ISODateTime | null; reason?: string | null; }
