import { api } from "./client";
import type { TelegramChannelRead, UUID } from "./types";

export const getTelegramChannel = (eid: UUID) =>
  api.get<TelegramChannelRead>(`/establishments/${eid}/channels/telegram`);

export const connectTelegram = (eid: UUID, botToken: string) =>
  api.put<TelegramChannelRead>(`/establishments/${eid}/channels/telegram`, { bot_token: botToken });

export const disconnectTelegram = (eid: UUID) =>
  api.delete<void>(`/establishments/${eid}/channels/telegram`);
