# Aurora · Agendamentos

Painel de agendamentos para salões/barbearias. Stack: **Vite + React 18 + TypeScript + Tailwind CSS + React Router**.

## Rodando localmente

Pré-requisitos: Node 18+ e npm (ou pnpm/yarn).

```bash
npm install
npm run dev
```

Abre em `http://localhost:5173`.

## Scripts

- `npm run dev` — servidor de desenvolvimento
- `npm run build` — build de produção (gera `dist/`)
- `npm run preview` — preview local do build

## Estrutura

```
src/
├── main.tsx              # entry point
├── App.tsx               # rotas + providers
├── index.css             # tailwind + tokens CSS (cores, tipografia)
├── components/           # primitives (Button, Input, Card, Sheet, ...)
│   ├── ui.tsx
│   ├── icons.tsx
│   ├── Shell.tsx
│   └── ToastProvider.tsx
├── screens/              # uma rota por arquivo
│   ├── Auth.tsx
│   ├── Dashboard.tsx
│   ├── WeekCalendar.tsx
│   ├── AppointmentsList.tsx
│   ├── Clients.tsx
│   ├── Services.tsx
│   ├── OperatingHours.tsx
│   ├── Templates.tsx
│   ├── Notifications.tsx
│   ├── Team.tsx
│   └── Settings.tsx
├── screens/sheets/       # AppointmentForm, AppointmentDetail, ClientForm
├── data/                 # mock data + tipos
│   ├── mock.ts
│   └── types.ts
├── store/                # store global em memória (substituirá API real)
│   └── useStore.ts
└── lib/                  # helpers (data, cores, formatação)
    ├── date.ts
    └── color.ts
```

## Rotas

| Rota              | Tela                |
| ----------------- | ------------------- |
| `/login`          | Login               |
| `/`               | Dashboard (hoje)    |
| `/calendar`       | Calendário semanal  |
| `/appointments`   | Lista de agendamentos |
| `/clients`        | Clientes            |
| `/services`       | Serviços            |
| `/hours`          | Horários            |
| `/templates`      | Templates de mensagem |
| `/notifications`  | Notificações        |
| `/team`           | Equipe              |
| `/settings`       | Configurações       |

## Próximos passos

1. Substituir o store em memória (`src/store/useStore.ts`) por chamadas à sua API real.
2. Adicionar autenticação real (a tela de login hoje só simula com `setTimeout`).
3. Plugar a Evolution API e Google Calendar nas configurações.
