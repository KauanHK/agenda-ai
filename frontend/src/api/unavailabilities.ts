import { api } from "./client";
import type {
  Paginated, UnavailabilityCreate, UnavailabilityRead, UnavailabilityUpdate, UUID,
} from "./types";

const base = (eid: UUID) => `/establishments/${eid}/unavailabilities`;

export const listUnavailabilities = (eid: UUID, q?: { starts_at_from?: string; starts_at_to?: string; page?: number; size?: number }) =>
  api.get<Paginated<UnavailabilityRead>>(`${base(eid)}`, q);

export const createUnavailability = (eid: UUID, body: UnavailabilityCreate) =>
  api.post<UnavailabilityRead>(`${base(eid)}`, body);

export const getUnavailability = (eid: UUID, id: UUID) =>
  api.get<UnavailabilityRead>(`${base(eid)}/${id}`);

export const updateUnavailability = (eid: UUID, id: UUID, body: UnavailabilityUpdate) =>
  api.patch<UnavailabilityRead>(`${base(eid)}/${id}`, body);

export const deleteUnavailability = (eid: UUID, id: UUID) =>
  api.delete<void>(`${base(eid)}/${id}`);
