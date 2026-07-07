import { api } from "./client";
import type { Paginated, ServiceCreate, ServiceRead, ServiceUpdate, UUID } from "./types";

const base = (eid: UUID) => `/establishments/${eid}/services`;

export const listServices = (eid: UUID, q?: { q?: string; is_active?: boolean; page?: number; size?: number }) =>
  api.get<Paginated<ServiceRead>>(`${base(eid)}`, q);

export const createService = (eid: UUID, body: ServiceCreate) =>
  api.post<ServiceRead>(`${base(eid)}`, body);

export const getService = (eid: UUID, id: UUID) =>
  api.get<ServiceRead>(`${base(eid)}/${id}`);

export const updateService = (eid: UUID, id: UUID, body: ServiceUpdate) =>
  api.patch<ServiceRead>(`${base(eid)}/${id}`, body);

export const deleteService = (eid: UUID, id: UUID) =>
  api.delete<void>(`${base(eid)}/${id}`);

export const activateService = (eid: UUID, id: UUID) =>
  api.post<ServiceRead>(`${base(eid)}/${id}/activate`);

export const deactivateService = (eid: UUID, id: UUID) =>
  api.post<ServiceRead>(`${base(eid)}/${id}/deactivate`);
