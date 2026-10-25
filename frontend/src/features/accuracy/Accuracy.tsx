import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { MetricCard } from "../../components/common/MetricCard";
import { StatusBadge } from "../../components/common/StatusBadge";
import { DataTable, type DataColumn } from "../../components/tables/DataTable";
import { chartColors } from "../../styles/theme";
import type { AccuracyPeriod, AccuracyResponse } from "../../types/accuracy";
import { chartAxisMw, chartTimeLabel, tooltipMw, tooltipSignedMw } from "../../utils/chartFormatters";
import { formatLondonDateTime, formatLondonTime } from "../../utils/date";
import { formatCount, formatMetricMw, formatMw, formatPercent, formatSignedMw, isMissingNumber } from "../../utils/formatters";
import "./Accuracy.css";

type AccuracyMetricsProps = {
  report: AccuracyResponse;
};

export function AccuracyMetrics({ report }: AccuracyMetricsProps) {
  const { metrics, coverage } = report;
  const mapeDetail =
    metrics.mape_percent === null
      ? "MAPE is unavailable when actual generation is too small to use as a percentage base."
      : `Calculated from ${formatCount(metrics.mape_observations)} periods. Matched pairs: ${formatCount(coverage.matched_periods)}.`;

  return (
    <section className="accuracy-metrics" aria-label="Accuracy metrics">
      <MetricCard label="MAE" value={formatMetricMw(metrics.mae_mw)} unit="MW" detail="Average magnitude of forecast error." />
      <MetricCard label="RMSE" value={formatMetricMw(metrics.rmse_mw)} unit="MW" detail="Penalises larger errors more than MAE." />
      <MetricCard
        label="Bias"
        value={formatSignedMw(metrics.bias_mw)}
        unit="MW"
        detail="Average of forecast minus actual. Positive is overforecast."
      />
      <MetricCard label="MAPE" value={formatPercent(metrics.mape_percent)} detail={mapeDetail} />
    </section>
  );
}

type ErrorChartProps = {
  rows: AccuracyPeriod[];
  series: "signed" | "absolute";
};

export function ErrorChart({ rows, series }: ErrorChartProps) {
  const data = rows.map((row) => ({
    startTime: row.start_time,
    label: chartTimeLabel(row.start_time),
    value: series === "signed" ? row.error_mw : row.absolute_error_mw,
  }));
  const ticks = data.filter((_, index) => index % 8 === 0).map((point) => point.label);

  return (
    <div className="error-chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke={chartColors.grid} vertical={false} />
          <XAxis dataKey="label" ticks={ticks} tick={{ fill: chartColors.axis, fontSize: 12 }} />
          <YAxis tickFormatter={chartAxisMw} tick={{ fill: chartColors.axis, fontSize: 12 }} width={56} />
          {series === "signed" ? <ReferenceLine y={0} stroke={chartColors.axis} /> : null}
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) {
                return null;
              }
              const point = payload[0].payload as (typeof data)[number];
              const value = series === "signed" ? tooltipSignedMw(point.value) : tooltipMw(point.value);
              return (
                <div className="error-chart__tooltip">
                  <p>{formatLondonDateTime(point.startTime)}</p>
                  <p>{value}</p>
                </div>
              );
            }}
          />
          <Bar dataKey="value" fill={chartColors.forecast}>
            {data.map((point) => (
              <Cell
                key={point.startTime}
                fill={
                  series === "absolute"
                    ? chartColors.forecast
                    : point.value !== null && point.value < 0
                      ? chartColors.errorNegative
                      : chartColors.errorPositive
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function status(row: AccuracyPeriod): { tone: "matched" | "missing" | "partial"; label: string } {
  const hasForecast = !isMissingNumber(row.forecast_generation_mw);
  const hasActual = !isMissingNumber(row.actual_generation_mw);
  if (hasForecast && hasActual) {
    return { tone: "matched", label: "Matched" };
  }
  if (!hasForecast) {
    return { tone: "missing", label: "No forecast" };
  }
  return { tone: "partial", label: "No actual" };
}

const columns: DataColumn<AccuracyPeriod>[] = [
  { key: "time", header: "Delivery time", render: (row) => formatLondonTime(row.start_time) },
  { key: "forecast", header: "Forecast MW", align: "right", render: (row) => formatMw(row.forecast_generation_mw) },
  { key: "actual", header: "Actual MW", align: "right", render: (row) => formatMw(row.actual_generation_mw) },
  { key: "error", header: "Error MW", align: "right", render: (row) => formatSignedMw(row.error_mw) },
  { key: "absolute", header: "Absolute MW", align: "right", render: (row) => formatMw(row.absolute_error_mw) },
  { key: "published", header: "Published", render: (row) => formatLondonDateTime(row.publish_time) },
  { key: "status", header: "Status", render: (row) => <StatusBadge {...status(row)} /> },
];

type AccuracyTableProps = {
  rows: AccuracyPeriod[];
};

export function AccuracyTable({ rows }: AccuracyTableProps) {
  return (
    <div className="accuracy-table">
      <DataTable
        columns={columns}
        rows={rows}
        rowKey={(row) => row.start_time}
        rowClassName={(row) => (isMissingNumber(row.error_mw) ? "is-missing" : undefined)}
      />
    </div>
  );
}
