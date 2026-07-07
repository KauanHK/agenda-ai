import { api } from "./client";
import type {
  MembershipCreateBody, MembershipRead, MembershipReadExpanded,
  MembershipUpdate, MembershipWithUser, PageQuery, Paginated, UUID,
} from "./types";

const base = (eid: UUID) => `/establishments/${eid}/members`;

export const listMembers = (eid: UUID, q?: PageQuery) =>
  api.get<Paginated<MembershipWithUser>>(`${base(eid)}`, q);

export const getMember = (eid: UUID, userId: UUID) =>
  api.get<MembershipReadExpanded>(`${base(eid)}/${userId}`);

export const addMember = (eid: UUID, body: MembershipCreateBody) =>
  api.post<MembershipRead>(`${base(eid)}`, body);

export const updateMember = (eid: UUID, userId: UUID, body: MembershipUpdate) =>
  api.patch<MembershipRead>(`${base(eid)}/${userId}`, body);

export const removeMember = (eid: UUID, userId: UUID) =>
  api.delete<void>(`${base(eid)}/${userId}`);

export const activateMember = (eid: UUID, userId: UUID) =>
  api.post<MembershipRead>(`${base(eid)}/${userId}/activate`);

export const deactivateMember = (eid: UUID, userId: UUID) =>
  api.post<MembershipRead>(`${base(eid)}/${userId}/deactivate`);
