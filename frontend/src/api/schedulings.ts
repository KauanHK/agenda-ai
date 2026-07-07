import { api } from "./client";
import type {
  CancelSchedulingRequest, Paginated, RescheduleRequest,
  SchedulingCreate, SchedulingExpandedRead, SchedulingRead,
  SchedulingSource, SchedulingStatus, SchedulingStatusLogRead, SchedulingUpdate, UUID,
} from "./types";

const base = (eid: UUID) => `/establishments/${eid}/schedulings`;

export const listSchedulings = (
  eid: UUID,
  q?: {
    status?: SchedulingStatus; source?: SchedulingSource;
    user_id?: UUID; client_id?: UUID; service_id?: UUID;
    starts_at_from?: string; starts_at_to?: string;
    page?: number; size?: number;
  },
) => api.get<Paginated<SchedulingRead>>(base(eid), q);

export const createScheduling = (eid: UUID, body: SchedulingCreate) =>
  api.post<SchedulingExpandedRead>(base(eid), body);

export const updateScheduling = (eid: UUID, id: UUID, body: SchedulingUpdate) =>
  api.patch<SchedulingExpandedRead>(`${base(eid)}/${id}`, body);

export const getScheduling = (eid: UUID, id: UUID) =>
  api.get<SchedulingExpandedRead>(`${base(eid)}/${id}`);

export const confirmScheduling = (eid: UUID, id: UUID) =>
  api.post<SchedulingExpandedRead>(`${base(eid)}/${id}/confirm`);

export const cancelScheduling = (eid: UUID, id: UUID, body: CancelSchedulingRequest) =>
  api.post<SchedulingExpandedRead>(`${base(eid)}/${id}/cancel`, body);

export const completeScheduling = (eid: UUID, id: UUID) =>
  api.post<SchedulingExpandedRead>(`${base(eid)}/${id}/complete`);

export const rescheduleScheduling = (eid: UUID, id: UUID, body: RescheduleRequest) =>
  api.post<SchedulingExpandedRead>(`${base(eid)}/${id}/reschedule`, body);

export const listSchedulingLogs = (eid: UUID, id: UUID, q?: { page?: number; size?: number }) =>
  api.get<Paginated<SchedulingStatusLogRead>>(`${base(eid)}/${id}/logs`, q);
