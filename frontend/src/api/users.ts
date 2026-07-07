import { api } from "./client";
import type { MembershipRead, Paginated, UserCreate, UserRead, UserRole, UserUpdate, UUID } from "./types";

export const me = () => api.get<UserRead>("/users/me");
export const updateMe = (body: UserUpdate) => api.patch<UserRead>("/users/me", body);

export const listUsers = (q?: { q?: string; role?: UserRole; is_active?: boolean; page?: number; size?: number }) =>
  api.get<Paginated<UserRead>>("/users/", q);

export const getUser = (id: UUID) => api.get<UserRead>(`/users/${id}`);
export const updateUser = (id: UUID, body: UserUpdate) => api.patch<UserRead>(`/users/${id}`, body);
export const deleteUser = (id: UUID) => api.delete<void>(`/users/${id}`);
export const createUser = (body: UserCreate) => api.post<UserRead>("/users", body);
export const activateUser = (id: UUID) => api.post<UserRead>(`/users/${id}/activate`);
export const deactivateUser = (id: UUID) => api.post<UserRead>(`/users/${id}/deactivate`);

export const listUserMemberships = (userId: UUID) =>
  api.get<MembershipRead[]>(`/users/${userId}/memberships`);
