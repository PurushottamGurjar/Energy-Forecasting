import { useQuery } from "@tanstack/react-query";
import { ChartPanel } from "../components/common/ChartPanel";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { Filter } from "../components/Filter/Filter";
import { Header } from "../components/Header/Header";
import { Sky } from "../components/Header/Sky";
import { AccuracyMetrics, AccuracyTable, ErrorChart } from "../features/accuracy/Accuracy";
import { ForecastChart } from "../features/forecasts/ForecastChart";
import { ForecastTable } from "../features/forecasts/ForecastTable";
import { useDashboardFilters } from "../hooks/useDashboardFilters";
import { accuracyQueryOptions } from "../services/accuracyApi";
import { forecastQueryOptions } from "../services/forecastApi";
import { formatLondonDateTime } from "../utils/date";
import { formatCount, formatMw } from "../utils/formatters";
import "./DashboardPage.css";

export function DashboardPage() {
  const filters = useDashboardFilters();

  return (
    <main className="dashboard">
      <Header view={filters.view} onViewChange={filters.setView} />
      <Sky />
      <Filter
        deliveryDate={filters.deliveryDate}
        decisionDate={filters.decisionDate}
        decisionClock={filters.decisionClock}
        showActual={filters.showActual}
        onDeliveryDateChange={filters.setDeliveryDate}
        onDecisionDateChange={filters.setDecisionDate}
        onDecisionClockChange={filters.setDecisionClock}
        onShowActualChange={filters.setShowActual}
        onGenerate={filters.generate}
      />
      <div className="dashboard__content">
        {!filters.deliveryDateValid ? <ErrorState message="Choose a delivery date in January 2026." /> : null}
        {filters.view === "forecast" ? (
          <ForecastPanel
            deliveryDate={filters.appliedDeliveryDate}
            decisionTime={filters.appliedDecisionTime}
            enabled={filters.deliveryDateValid}
            showActual={filters.appliedShowActual}
            requestId={filters.appliedRequestId}
          />
        ) : (
          <AccuracyPanel
            deliveryDate={filters.appliedDeliveryDate}
            decisionTime={filters.appliedDecisionTime}
            enabled={filters.deliveryDateValid}
            requestId={filters.appliedRequestId}
          />
        )}
      </div>
    </main>
  );
}

type PanelProps = {
  deliveryDate: string;
  decisionTime: string;
  enabled: boolean;
  showActual?: boolean;
  requestId: number;
};

function ForecastPanel({ deliveryDate, decisionTime, enabled, showActual = true, requestId }: PanelProps) {
  const options = forecastQueryOptions(deliveryDate, decisionTime, showActual);
  const query = useQuery({
    ...options,
    queryKey: [...options.queryKey, String(requestId)],
    enabled,
  });
  const published = query.data?.data.find((row) => row.publish_time)?.publish_time ?? null;

  if (query.isLoading) {
    return <LoadingState label="Loading forecasts" />;
  }
  if (query.isError) {
    return <ErrorState message={query.error.message} onRetry={() => void query.refetch()} />;
  }
  if (!query.data) {
    return null;
  }

  const { summary } = query.data;

  return (
    <>
      <section className="overview" aria-label="Overview">
        <div className="overview__grid">
          <article className="overview__card">
            <p className="overview__label">Latest publication</p>
            <p className="overview__value">{published ? formatLondonDateTime(published) : "None"}</p>
          </article>
          <article className="overview__card">
            <p className="overview__label">Total forecast</p>
            <p className="overview__value tabular">
              {formatMw(
                summary.average_forecast_mw == null
                  ? null
                  : summary.average_forecast_mw * summary.periods_expected,
              )}
              <span>MW</span>
            </p>
          </article>
          <article className="overview__card">
            <p className="overview__label">Periods with forecast</p>
            <p className="overview__value tabular">
              {formatCount(summary.periods_with_forecast)}
              <span>/ {formatCount(summary.periods_expected)}</span>
            </p>
          </article>
          <article className="overview__card">
            <p className="overview__label">Periods without forecast</p>
            <p className="overview__value tabular">{formatCount(summary.missing_forecast_periods)}</p>
          </article>
        </div>
      </section>
      <ChartPanel
        title={showActual ? "Selected forecast and actual generation" : "Selected forecast"}
        subtitle={
          showActual
            ? "Actuals are included when FUELHH has a value for the same start time."
            : "National wind forecast known at the decision cutoff."
        }
      >
        <ForecastChart rows={query.data.data} showActual={showActual} />
      </ChartPanel>
      <ForecastTable rows={query.data.data} showActual={showActual} />
    </>
  );
}

function AccuracyPanel({ deliveryDate, decisionTime, enabled, requestId }: PanelProps) {
  const options = accuracyQueryOptions(deliveryDate, decisionTime);
  const query = useQuery({
    ...options,
    queryKey: [...options.queryKey, String(requestId)],
    enabled,
  });

  if (query.isLoading) {
    return <LoadingState label="Loading accuracy" />;
  }
  if (query.isError) {
    return <ErrorState message={query.error.message} onRetry={() => void query.refetch()} />;
  }
  if (!query.data) {
    return null;
  }

  return (
    <>
      <AccuracyMetrics report={query.data} />
      <div className="dashboard__charts">
        <ChartPanel title="Signed error" subtitle="Positive bars overforecast wind. Negative bars underforecast it.">
          <ErrorChart rows={query.data.data} series="signed" />
        </ChartPanel>
        <ChartPanel title="Absolute error" subtitle="The size of the miss in each matched hour, in MW.">
          <ErrorChart rows={query.data.data} series="absolute" />
        </ChartPanel>
      </div>
      <AccuracyTable rows={query.data.data} />
    </>
  );
}
