import { api } from "./client";
import type {
  DashboardResponse, EstablishmentCreate, EstablishmentRead, EstablishmentUpdate,
  Paginated, UUID,
} from "./types";

export const listEstablishments = (q?: { name?: string; cnpj?: string; timezone?: string; page?: number; size?: number }) =>
  api.get<Paginated<EstablishmentRead>>("/establishments", q);

export const createEstablishment = (body: EstablishmentCreate) =>
  api.post<EstablishmentRead>("/establishments", body);

export const getEstablishment = (id: UUID) =>
  api.get<EstablishmentRead>(`/establishments/${id}`);

export const updateEstablishment = (id: UUID, body: EstablishmentUpdate) =>
  api.patch<EstablishmentRead>(`/establishments/${id}`, body);

export const deleteEstablishment = (id: UUID) =>
  api.delete<void>(`/establishments/${id}`);

export const activateEstablishment = (id: UUID) =>
  api.post<EstablishmentRead>(`/establishments/${id}/activate`);

export const deactivateEstablishment = (id: UUID) =>
  api.post<EstablishmentRead>(`/establishments/${id}/deactivate`);

export const getDashboard = (id: UUID, date: string) =>
  api.get<DashboardResponse>(`/establishments/${id}/dashboard`, { start_date: date, end_date: date });
