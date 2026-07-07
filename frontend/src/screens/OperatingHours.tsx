import * as React from "react";
import * as ohApi from "@/api/operating-hours";
import { useEstablishmentId } from "@/store/auth";
import { Button, Card, PageHeader, Toggle } from "@/components/ui";
import { useToast } from "@/components/ToastProvider";
import { WEEKDAYS_LONG } from "@/lib/date";

interface TimeSlot {
  start_time: string;
  end_time: string;
}

interface DayState {
  weekday: number;
  is_open: boolean;
  slots: TimeSlot[];
}

const defaultSlot = (): TimeSlot => ({ start_time: "09:00", end_time: "18:00" });

const defaultDays = (): DayState[] =>
  Array.from({ length: 7 }, (_, i) => ({
    weekday: i,
    is_open: i >= 1 && i <= 5,
    slots: [defaultSlot()],
  }));

const trimSec = (t: string) => (t?.length >= 5 ? t.slice(0, 5) : t);

const timeInputStyle: React.CSSProperties = {
  border: "1px solid var(--border)",
  background: "var(--surface)",
  padding: "6px 10px",
  borderRadius: 8,
  fontSize: 13,
  fontFamily: "inherit",
  color: "var(--text)",
  minWidth: 0,
  width: 112,
};

interface SlotListProps {
  day: DayState;
  dayIdx: number;
  onUpdate: (dayIdx: number, slotIdx: number, patch: Partial<TimeSlot>) => void;
  onAdd: (dayIdx: number) => void;
  onRemove: (dayIdx: number, slotIdx: number) => void;
}

const SlotList: React.FC<SlotListProps> = ({ day, dayIdx, onUpdate, onAdd, onRemove }) => {
  if (!day.is_open) {
    return <div style={{ fontSize: 13, color: "var(--text-dim)", paddingTop: 6 }}>Fechado</div>;
  }
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {day.slots.map((slot, slotIdx) => (
        <div key={slotIdx} style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
          <input
            type="time"
            value={slot.start_time}
            onChange={(e) => onUpdate(dayIdx, slotIdx, { start_time: e.target.value })}
            style={timeInputStyle}
          />
          <span style={{ color: "var(--text-dim)", flexShrink: 0 }}>—</span>
          <input
            type="time"
            value={slot.end_time}
            onChange={(e) => onUpdate(dayIdx, slotIdx, { end_time: e.target.value })}
            style={timeInputStyle}
          />
          {day.slots.length > 1 && (
            <button
              onClick={() => onRemove(dayIdx, slotIdx)}
              title="Remover faixa"
              style={{
                background: "none", border: "none", cursor: "pointer",
                color: "var(--text-dim)", fontSize: 16, lineHeight: 1,
                padding: "2px 4px", borderRadius: 4, flexShrink: 0,
              }}
            >
              ×
            </button>
          )}
        </div>
      ))}
      <button
        onClick={() => onAdd(dayIdx)}
        style={{
          background: "none", border: "none", cursor: "pointer",
          color: "var(--color-primary)", fontSize: 13, fontFamily: "inherit",
          textAlign: "left", padding: "2px 0", width: "fit-content",
        }}
      >
        + Adicionar faixa
      </button>
    </div>
  );
};

export const OperatingHours: React.FC = () => {
  const eid = useEstablishmentId();
  const [days, setDays] = React.useState<DayState[]>(defaultDays);
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [isDesktop, setIsDesktop] = React.useState(() => window.matchMedia("(min-width: 900px)").matches);
  const toast = useToast();

  React.useEffect(() => {
    const mq = window.matchMedia("(min-width: 900px)");
    const h = (e: MediaQueryListEvent) => setIsDesktop(e.matches);
    mq.addEventListener("change", h);
    return () => mq.removeEventListener("change", h);
  }, []);

  React.useEffect(() => {
    (async () => {
      try {
        const list = await ohApi.getOperatingHours(eid);
        const next: DayState[] = Array.from({ length: 7 }, (_, i) => ({
          weekday: i, is_open: false, slots: [],
        }));
        list.forEach((h) => {
          const d = next[h.weekday];
          if (!d) return;
          d.is_open = true;
          d.slots.push({ start_time: trimSec(h.start_time), end_time: trimSec(h.end_time) });
        });
        setDays(next);
      } catch (e: any) {
        toast(e?.message ?? "Erro ao carregar horários", "danger");
      } finally {
        setLoading(false);
      }
    })();
  }, [eid, toast]);

  const updateSlot = (dayIdx: number, slotIdx: number, patch: Partial<TimeSlot>) =>
    setDays((d) =>
      d.map((x, i) =>
        i !== dayIdx
          ? x
          : { ...x, slots: x.slots.map((s, j) => (j === slotIdx ? { ...s, ...patch } : s)) }
      )
    );

  const addSlot = (dayIdx: number) =>
    setDays((d) =>
      d.map((x, i) => (i !== dayIdx ? x : { ...x, slots: [...x.slots, defaultSlot()] }))
    );

  const removeSlot = (dayIdx: number, slotIdx: number) =>
    setDays((d) =>
      d.map((x, i) =>
        i !== dayIdx ? x : { ...x, slots: x.slots.filter((_, j) => j !== slotIdx) }
      )
    );

  const toggleDay = (dayIdx: number, open: boolean) =>
    setDays((d) =>
      d.map((x, i) =>
        i !== dayIdx
          ? x
          : { ...x, is_open: open, slots: x.slots.length === 0 ? [defaultSlot()] : x.slots }
      )
    );

  const save = async () => {
    setSaving(true);
    try {
      const items = days
        .filter((d) => d.is_open && d.slots.length > 0)
        .flatMap((d) =>
          d.slots.map((s) => ({ weekday: d.weekday, start_time: s.start_time, end_time: s.end_time }))
        );
      await ohApi.updateOperatingHours(eid, { items });
      toast("Horários salvos!");
    } catch (e: any) {
      toast(e?.message ?? "Erro ao salvar", "danger");
    } finally {
      setSaving(false);
    }
  };

  if (loading)
    return (
      <div className="page" style={{ padding: "var(--page-pad)", color: "var(--text-dim)" }}>
        Carregando…
      </div>
    );

  return (
    <div className="page" style={{ padding: "var(--page-pad)" }}>
      <PageHeader title="Horários" subtitle="Janela de funcionamento por dia da semana" />
      <Card padded={false}>
        {days.map((day, dayIdx) => (
          <div
            key={day.weekday}
            style={{
              padding: "14px 16px",
              borderBottom: dayIdx < days.length - 1 ? "1px solid var(--border)" : 0,
            }}
          >
            {isDesktop ? (
              /* Desktop: 3 colunas */
              <div style={{ display: "grid", gridTemplateColumns: "110px 1fr auto", alignItems: "start", gap: "8px 12px" }}>
                <div style={{ fontSize: 14, fontWeight: 500, paddingTop: day.is_open ? 8 : 6 }}>
                  {WEEKDAYS_LONG[day.weekday]}
                </div>
                <SlotList day={day} dayIdx={dayIdx} onUpdate={updateSlot} onAdd={addSlot} onRemove={removeSlot} />
                <div style={{ paddingTop: day.is_open ? 6 : 4 }}>
                  <Toggle checked={day.is_open} onChange={(v) => toggleDay(dayIdx, v)} />
                </div>
              </div>
            ) : (
              /* Mobile: nome + toggle em linha, slots embaixo */
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div style={{ fontSize: 14, fontWeight: 500 }}>{WEEKDAYS_LONG[day.weekday]}</div>
                  <Toggle checked={day.is_open} onChange={(v) => toggleDay(dayIdx, v)} />
                </div>
                {day.is_open && (
                  <SlotList day={day} dayIdx={dayIdx} onUpdate={updateSlot} onAdd={addSlot} onRemove={removeSlot} />
                )}
                {!day.is_open && (
                  <div style={{ fontSize: 13, color: "var(--text-dim)" }}>Fechado</div>
                )}
              </div>
            )}
          </div>
        ))}
      </Card>
      <div style={{
        marginTop: 16,
        display: "flex",
        justifyContent: isDesktop ? "flex-end" : "stretch",
        paddingBottom: isDesktop ? 0 : "var(--bottom-nav-h)",
      }}>
        <Button onClick={save} disabled={saving} fullWidth={!isDesktop}>
          {saving ? "Salvando…" : "Salvar alterações"}
        </Button>
      </div>
    </div>
  );
};
