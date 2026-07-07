export const WEEKDAYS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];
export const WEEKDAYS_LONG = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];
export const MONTHS = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

export const fmtTime = (iso: string | Date) => {
  const d = new Date(iso);
  return d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
};

export const fmtDate = (iso: string | Date) => {
  const d = new Date(iso);
  return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;
};

export const fmtDateLong = (iso: string | Date) => {
  const d = new Date(iso);
  return `${WEEKDAYS_LONG[(d.getDay() + 6) % 7]}, ${d.getDate()} de ${MONTHS[d.getMonth()].toLowerCase()}`;
};

export const fmtMoney = (v: number) => `R$ ${v.toFixed(2).replace(".", ",")}`;

export const sameDay = (a: string | Date, b: string | Date) => {
  const da = new Date(a), db = new Date(b);
  return da.getFullYear() === db.getFullYear() &&
    da.getMonth() === db.getMonth() &&
    da.getDate() === db.getDate();
};

// Monday=0 .. Sunday=6
export const getWeekday = (d: string | Date) => (new Date(d).getDay() + 6) % 7;
