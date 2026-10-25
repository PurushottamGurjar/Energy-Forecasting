import type { AnalysisView } from "../../hooks/useDashboardFilters";
import "./Header.css";

type HeaderProps = {
  view: AnalysisView;
  onViewChange: (value: AnalysisView) => void;
};

export function Header({ view, onViewChange }: HeaderProps) {
  return (
    <header className="page-header">
      <div className="page-header__identity">
        <span className="page-header__mark" aria-hidden="true">
          <BarChartIcon />
        </span>
        <div>
          <h1>Windie: Wind Energy Insights</h1>
          <p>Compare forecast vs actual power generation</p>
        </div>
      </div>
      <div className="page-header__views" role="group" aria-label="Analysis">
        <button
          type="button"
          className={view === "forecast" ? "is-active" : undefined}
          aria-pressed={view === "forecast"}
          onClick={() => onViewChange("forecast")}
        >
          <BarChartIcon />
          Forecast analysis
        </button>
        <button
          type="button"
          className={view === "accuracy" ? "is-active" : undefined}
          aria-pressed={view === "accuracy"}
          onClick={() => onViewChange("accuracy")}
        >
          <TargetIcon />
          Accuracy analysis
        </button>
      </div>
    </header>
  );
}

function BarChartIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 20V10" />
      <path d="M10 20V4" />
      <path d="M16 20v-7" />
      <path d="M22 20H2" />
    </svg>
  );
}

function TargetIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="8" />
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v3" />
      <path d="M12 19v3" />
      <path d="M2 12h3" />
      <path d="M19 12h3" />
    </svg>
  );
}
