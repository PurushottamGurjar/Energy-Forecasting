const LONDON = "Europe/London";

const DELIVERY_START = "2026-01-01";
const DELIVERY_END = "2026-01-31";

export const DEFAULT_DELIVERY_DATE = "2026-01-15";
export const DEFAULT_DECISION_DATE = "2026-01-14";
export const DEFAULT_DECISION_CLOCK = "13:00";

export function isJanuary2026(value: string): boolean {
  return value >= DELIVERY_START && value <= DELIVERY_END;
}

function timeZoneOffsetMinutes(instant: Date, timeZone: string): number {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hourCycle: "h23",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).formatToParts(instant);
  const value: Record<string, string> = {};
  for (const part of parts) {
    if (part.type !== "literal") {
      value[part.type] = part.value;
    }
  }
  const asUtc = Date.UTC(
    Number(value.year),
    Number(value.month) - 1,
    Number(value.day),
    Number(value.hour),
    Number(value.minute),
    Number(value.second),
  );
  return (asUtc - instant.getTime()) / 60_000;
}

export function londonLocalToUtcIso(date: string, time: string): string {
  const [year, month, day] = date.split("-").map(Number);
  const [hour, minute] = time.split(":").map(Number);
  const utcGuess = new Date(Date.UTC(year, month - 1, day, hour, minute, 0));
  const offset = timeZoneOffsetMinutes(utcGuess, LONDON);
  const utc = new Date(utcGuess.getTime() - offset * 60_000);
  return utc.toISOString().replace(/\.\d{3}Z$/, "Z");
}

const dateTimeFormat = new Intl.DateTimeFormat("en-GB", {
  timeZone: LONDON,
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
  timeZoneName: "short",
});

const timeFormat = new Intl.DateTimeFormat("en-GB", {
  timeZone: LONDON,
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

const dayFormat = new Intl.DateTimeFormat("en-GB", {
  timeZone: LONDON,
  day: "2-digit",
  month: "short",
  year: "numeric",
});

export function formatLondonDateTime(value: string | null): string {
  if (!value) {
    return "—";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "—";
  }
  return dateTimeFormat.format(parsed);
}

export function formatLondonTime(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "—";
  }
  return timeFormat.format(parsed);
}

export function formatLondonDay(value: string): string {
  const parsed = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return dayFormat.format(parsed);
}
