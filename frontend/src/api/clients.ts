import { api } from "./client";
import type { ClientCreate, ClientRead, ClientUpdate, Paginated, UUID } from "./types";

const base = (eid: UUID) => `/establishments/${eid}/clients`;

export const listClients = (eid: UUID, q?: { q?: string; is_active?: boolean; page?: number; size?: number }) =>
  api.get<Paginated<ClientRead>>(`${base(eid)}`, q);

export const createClient = (eid: UUID, body: ClientCreate) =>
  api.post<ClientRead>(`${base(eid)}`, body);

export const getClient = (eid: UUID, id: UUID) =>
  api.get<ClientRead>(`${base(eid)}/${id}`);

export const updateClient = (eid: UUID, id: UUID, body: ClientUpdate) =>
  api.patch<ClientRead>(`${base(eid)}/${id}`, body);

export const deleteClient = (eid: UUID, id: UUID) =>
  api.delete<void>(`${base(eid)}/${id}`);

export const activateClient = (eid: UUID, id: UUID) =>
  api.post<ClientRead>(`${base(eid)}/${id}/activate`);

export const deactivateClient = (eid: UUID, id: UUID) =>
  api.post<ClientRead>(`${base(eid)}/${id}/deactivate`);
