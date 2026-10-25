import "./LoadingState.css";

export function LoadingState({ label = "Loading wind data" }: { label?: string }) {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <p className="loading-state__label">{label}</p>
      <div className="loading-state__row">
        <span className="loading-state__card" />
        <span className="loading-state__card" />
        <span className="loading-state__card" />
        <span className="loading-state__card" />
      </div>
      <span className="loading-state__panel" />
    </div>
  );
}
