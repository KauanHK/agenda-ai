import { api } from "./client";
import type {
  MessagingTemplateCreate, MessagingTemplateRead, MessagingTemplateUpdate,
  Paginated, UUID,
} from "./types";

const base = (eid: UUID) => `/establishments/${eid}/messaging/templates`;

export const listTemplates = (eid: UUID, q?: { is_active?: boolean; service_id?: UUID; q?: string; page?: number; size?: number }) =>
  api.get<Paginated<MessagingTemplateRead>>(base(eid), q);

export const createTemplate = (eid: UUID, body: MessagingTemplateCreate) =>
  api.post<MessagingTemplateRead>(base(eid), body);

export const getTemplate = (eid: UUID, id: UUID) =>
  api.get<MessagingTemplateRead>(`${base(eid)}/${id}`);

export const updateTemplate = (eid: UUID, id: UUID, body: MessagingTemplateUpdate) =>
  api.patch<MessagingTemplateRead>(`${base(eid)}/${id}`, body);

export const deleteTemplate = (eid: UUID, id: UUID) =>
  api.delete<void>(`${base(eid)}/${id}`);

export const linkService = (eid: UUID, tid: UUID, sid: UUID) =>
  api.post<void>(`${base(eid)}/${tid}/services/${sid}`);

export const unlinkService = (eid: UUID, tid: UUID, sid: UUID) =>
  api.delete<void>(`${base(eid)}/${tid}/services/${sid}`);

export const activateTemplateService = (eid: UUID, tid: UUID, sid: UUID) =>
  api.post<void>(`${base(eid)}/${tid}/services/${sid}/activate`);

export const deactivateTemplateService = (eid: UUID, tid: UUID, sid: UUID) =>
  api.post<void>(`${base(eid)}/${tid}/services/${sid}/deactivate`);
