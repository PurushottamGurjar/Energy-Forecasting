import type { ReactNode } from "react";
import "./ChartPanel.css";

type ChartPanelProps = {
  title: string;
  subtitle: string;
  children: ReactNode;
};

export function ChartPanel({ title, subtitle, children }: ChartPanelProps) {
  return (
    <section className="chart-panel">
      <header>
        <h2>{title}</h2>
        <p>{subtitle}</p>
      </header>
      <div className="chart-panel__body">{children}</div>
    </section>
  );
}
