import "./StatusBadge.css";

type StatusBadgeProps = {
  tone: "matched" | "missing" | "partial";
  label: string;
};

export function StatusBadge({ tone, label }: StatusBadgeProps) {
  return <span className={`status-badge status-badge--${tone}`}>{label}</span>;
}
