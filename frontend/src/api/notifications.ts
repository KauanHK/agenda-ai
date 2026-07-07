import { api } from "./client";
import type { NotificationStatus, Paginated, SchedulingNotificationRead, UUID } from "./types";

const base = (eid: UUID) => `/establishments/${eid}/messaging/notifications`;

export const listNotifications = (
  eid: UUID,
  q?: {
    scheduling_id?: UUID; template_id?: UUID; status?: NotificationStatus;
    sent_at_from?: string; sent_at_to?: string;
    page?: number; size?: number;
  },
) => api.get<Paginated<SchedulingNotificationRead>>(base(eid), q);

export const getNotification = (eid: UUID, id: UUID) =>
  api.get<SchedulingNotificationRead>(`${base(eid)}/${id}`);

export const cancelNotification = (eid: UUID, id: UUID) =>
  api.post<SchedulingNotificationRead>(`${base(eid)}/${id}/cancel`);
