import { api } from "./client";
import type { OperatingHourRead, OperatingHoursUpdate, UUID } from "./types";

export const getOperatingHours = (eid: UUID) =>
  api.get<OperatingHourRead[]>(`/establishments/${eid}/operating-hours`);

export const updateOperatingHours = (eid: UUID, body: OperatingHoursUpdate) =>
  api.put<OperatingHourRead[]>(`/establishments/${eid}/operating-hours`, body);
