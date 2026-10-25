import "./MetricCard.css";

type MetricCardProps = {
  label: string;
  value: string;
  unit?: string;
  detail: string;
};

export function MetricCard({ label, value, unit, detail }: MetricCardProps) {
  return (
    <article className="metric-card">
      <p className="metric-card__label">{label}</p>
      <p className="metric-card__value tabular">
        {value}
        {unit && value !== "N/A" ? <span>{unit}</span> : null}
      </p>
      <p className="metric-card__detail">{detail}</p>
    </article>
  );
}
