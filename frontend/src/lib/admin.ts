// Common Brazilian timezones offered in admin establishment forms.
// IANA names + a friendly Portuguese label for the dropdown.

export const BR_TIMEZONES: { value: string; label: string }[] = [
  { value: "America/Sao_Paulo",  label: "Brasília (GMT−03:00)" },
  { value: "America/Bahia",      label: "Salvador (GMT−03:00)" },
  { value: "America/Fortaleza",  label: "Fortaleza (GMT−03:00)" },
  { value: "America/Recife",     label: "Recife (GMT−03:00)" },
  { value: "America/Belem",      label: "Belém (GMT−03:00)" },
  { value: "America/Maceio",     label: "Maceió (GMT−03:00)" },
  { value: "America/Araguaina",  label: "Araguaína (GMT−03:00)" },
  { value: "America/Cuiaba",     label: "Cuiabá (GMT−04:00)" },
  { value: "America/Campo_Grande", label: "Campo Grande (GMT−04:00)" },
  { value: "America/Porto_Velho", label: "Porto Velho (GMT−04:00)" },
  { value: "America/Boa_Vista",  label: "Boa Vista (GMT−04:00)" },
  { value: "America/Manaus",     label: "Manaus (GMT−04:00)" },
  { value: "America/Rio_Branco", label: "Rio Branco (GMT−05:00)" },
  { value: "America/Noronha",    label: "Fernando de Noronha (GMT−02:00)" },
];

const TZ_VALUES = new Set(BR_TIMEZONES.map((t) => t.value));

/** Returns the dropdown options, including the current value if it
 *  isn't one of our presets — so editing legacy data won't blow it
 *  away by selecting the empty option on save. */
export function timezoneOptions(currentValue?: string) {
  if (currentValue && !TZ_VALUES.has(currentValue)) {
    return [{ value: currentValue, label: currentValue }, ...BR_TIMEZONES];
  }
  return BR_TIMEZONES;
}

/** Format CNPJ "12345678000190" → "12.345.678/0001-90". */
export function fmtCnpj(raw: string): string {
  const d = (raw || "").replace(/\D/g, "");
  if (d.length !== 14) return raw;
  return `${d.slice(0,2)}.${d.slice(2,5)}.${d.slice(5,8)}/${d.slice(8,12)}-${d.slice(12)}`;
}

/** Format CPF "12345678901" → "123.456.789-01". */
export function fmtCpf(raw: string): string {
  const d = (raw || "").replace(/\D/g, "");
  if (d.length !== 11) return raw;
  return `${d.slice(0,3)}.${d.slice(3,6)}.${d.slice(6,9)}-${d.slice(9)}`;
}

export function fmtDocument(raw: string, type: "cpf" | "cnpj"): string {
  return type === "cnpj" ? fmtCnpj(raw) : fmtCpf(raw);
}
