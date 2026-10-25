const numberFormat = new Intl.NumberFormat("en-GB", {
  maximumFractionDigits: 1,
  minimumFractionDigits: 0,
});

const metricFormat = new Intl.NumberFormat("en-GB", {
  maximumFractionDigits: 1,
  minimumFractionDigits: 1,
});

export function isMissingNumber(value: number | null | undefined): value is null | undefined {
  return value === null || value === undefined || Number.isNaN(value);
}

export function formatMw(value: number | null | undefined): string {
  if (isMissingNumber(value)) {
    return "—";
  }
  return numberFormat.format(value);
}

export function formatMetricMw(value: number | null | undefined): string {
  if (isMissingNumber(value)) {
    return "N/A";
  }
  return metricFormat.format(value);
}

export function formatSignedMw(value: number | null | undefined): string {
  if (isMissingNumber(value)) {
    return "N/A";
  }
  const formatted = metricFormat.format(Math.abs(value));
  if (value > 0) {
    return `+${formatted}`;
  }
  if (value < 0) {
    return `−${formatted}`;
  }
  return formatted;
}

export function formatPercent(value: number | null | undefined): string {
  if (isMissingNumber(value)) {
    return "N/A";
  }
  return `${metricFormat.format(value)}%`;
}

export function formatCount(value: number): string {
  return new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 }).format(value);
}
