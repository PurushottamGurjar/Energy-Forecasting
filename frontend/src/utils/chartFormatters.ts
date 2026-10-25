import { formatLondonTime } from "./date";
import { formatMw, formatSignedMw, isMissingNumber } from "./formatters";

export function chartTimeLabel(startTime: string): string {
  return formatLondonTime(startTime);
}

export function chartAxisMw(value: number): string {
  return new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0, notation: "compact" }).format(value);
}

export function tooltipMw(value: number | null): string {
  if (isMissingNumber(value)) {
    return "—";
  }
  return `${formatMw(value)} MW`;
}

export function tooltipSignedMw(value: number | null): string {
  if (isMissingNumber(value)) {
    return "—";
  }
  return `${formatSignedMw(value)} MW`;
}
