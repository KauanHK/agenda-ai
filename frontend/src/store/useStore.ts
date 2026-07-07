import { create } from "./createStore";
import * as mock from "@/data/mock";
import type { Client, Notification, OperatingHour, Scheduling, Service, Template } from "@/data/types";

interface Store {
  schedulings: Scheduling[];
  clients: Client[];
  services: Service[];
  templates: Template[];
  notifications: Notification[];
  operatingHours: OperatingHour[];

  saveScheduling: (s: Partial<Scheduling> & { id?: string }) => void;
  deleteScheduling: (id: string) => void;
  setSchedulingStatus: (id: string, status: Scheduling["status"]) => void;

  saveClient: (c: Partial<Client> & { id?: string | null }) => void;
  deactivateClient: (id: string) => void;

  saveService: (s: Partial<Service> & { id?: string }) => void;
  saveTemplate: (t: Partial<Template> & { id?: string }) => void;
  saveOperatingHour: (idx: number, patch: Partial<OperatingHour>) => void;
}

export const useStore = create<Store>((set) => ({
  schedulings: mock.schedulings,
  clients: mock.clients,
  services: mock.services,
  templates: mock.templates,
  notifications: mock.notifications,
  operatingHours: mock.operatingHours,

  saveScheduling: (s) =>
    set((st) => ({
      schedulings: s.id
        ? st.schedulings.map((x) => (x.id === s.id ? { ...x, ...(s as Scheduling) } : x))
        : [...st.schedulings, { ...(s as Scheduling), id: `sc-${Date.now()}` }],
    })),

  deleteScheduling: (id) =>
    set((st) => ({ schedulings: st.schedulings.filter((x) => x.id !== id) })),

  setSchedulingStatus: (id, status) =>
    set((st) => ({
      schedulings: st.schedulings.map((x) => (x.id === id ? { ...x, status } : x)),
    })),

  saveClient: (c) =>
    set((st) => ({
      clients: c.id
        ? st.clients.map((x) => (x.id === c.id ? { ...x, ...(c as Client) } : x))
        : [...st.clients, { ...(c as Client), id: `c-${Date.now()}`, last_visit: null }],
    })),

  deactivateClient: (id) =>
    set((st) => ({ clients: st.clients.map((x) => (x.id === id ? { ...x, is_active: false } : x)) })),

  saveService: (s) =>
    set((st) => ({
      services: s.id
        ? st.services.map((x) => (x.id === s.id ? { ...x, ...(s as Service) } : x))
        : [...st.services, { ...(s as Service), id: `s-${Date.now()}`, is_active: true }],
    })),

  saveTemplate: (t) =>
    set((st) => ({
      templates: t.id
        ? st.templates.map((x) => (x.id === t.id ? { ...x, ...(t as Template) } : x))
        : [...st.templates, { ...(t as Template), id: `t-${Date.now()}`, is_active: true }],
    })),

  saveOperatingHour: (idx, patch) =>
    set((st) => ({
      operatingHours: st.operatingHours.map((h, i) => (i === idx ? { ...h, ...patch } : h)),
    })),
}));
