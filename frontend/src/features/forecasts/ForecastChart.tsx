import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { chartColors } from "../../styles/theme";
import type { ForecastPeriod } from "../../types/forecast";
import { chartAxisMw, chartTimeLabel, tooltipMw } from "../../utils/chartFormatters";
import { formatLondonDateTime } from "../../utils/date";
import "./ForecastChart.css";

type ForecastChartProps = {
  rows: ForecastPeriod[];
  showActual: boolean;
};

export function ForecastChart({ rows, showActual }: ForecastChartProps) {
  const data = rows.map((row) => ({
    startTime: row.start_time,
    label: chartTimeLabel(row.start_time),
    forecast: row.forecast_generation_mw,
    actual: row.actual_generation_mw,
  }));
  const ticks = data.filter((_, index) => index % 8 === 0).map((point) => point.label);

  return (
    <div className="forecast-chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke={chartColors.grid} vertical={false} />
          <XAxis dataKey="label" ticks={ticks} tick={{ fill: chartColors.axis, fontSize: 12 }} />
          <YAxis tickFormatter={chartAxisMw} tick={{ fill: chartColors.axis, fontSize: 12 }} width={56} />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) {
                return null;
              }
              const point = payload[0].payload as (typeof data)[number];
              return (
                <div className="forecast-chart__tooltip">
                  <p>{formatLondonDateTime(point.startTime)}</p>
                  <p>Forecast {tooltipMw(point.forecast)}</p>
                  {showActual ? <p>Actual {tooltipMw(point.actual)}</p> : null}
                </div>
              );
            }}
          />
          <Legend />
          <Line type="monotone" dataKey="forecast" name="Forecast" stroke={chartColors.forecast} strokeWidth={2} dot={false} connectNulls={false} />
          {showActual ? (
            <Line type="monotone" dataKey="actual" name="Actual" stroke={chartColors.actual} strokeWidth={2} dot={false} connectNulls={false} />
          ) : null}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
