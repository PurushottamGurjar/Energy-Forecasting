import { DataTable, type DataColumn } from "../../components/tables/DataTable";
import { StatusBadge } from "../../components/common/StatusBadge";
import type { ForecastPeriod } from "../../types/forecast";
import { formatLondonDateTime, formatLondonTime } from "../../utils/date";
import { formatMw, formatSignedMw, isMissingNumber } from "../../utils/formatters";
import "./ForecastTable.css";

function rowStatus(row: ForecastPeriod, showActual: boolean): { tone: "matched" | "missing" | "partial"; label: string } {
  const hasForecast = !isMissingNumber(row.forecast_generation_mw);
  if (!showActual) {
    return hasForecast ? { tone: "matched", label: "Forecast" } : { tone: "missing", label: "No forecast" };
  }
  const hasActual = !isMissingNumber(row.actual_generation_mw);
  if (hasForecast && hasActual) {
    return { tone: "matched", label: "Matched" };
  }
  if (!hasForecast && hasActual) {
    return { tone: "missing", label: "No forecast" };
  }
  if (hasForecast && !hasActual) {
    return { tone: "partial", label: "No actual" };
  }
  return { tone: "missing", label: "Missing" };
}

function displayError(row: ForecastPeriod): number | null {
  if (isMissingNumber(row.forecast_generation_mw) || isMissingNumber(row.actual_generation_mw)) {
    return null;
  }
  return row.forecast_generation_mw - row.actual_generation_mw;
}

type ForecastTableProps = {
  rows: ForecastPeriod[];
  showActual: boolean;
};

export function ForecastTable({ rows, showActual }: ForecastTableProps) {
  const columns: DataColumn<ForecastPeriod>[] = [
    { key: "time", header: "Delivery time", render: (row) => formatLondonTime(row.start_time) },
    { key: "forecast", header: "Forecast MW", align: "right", render: (row) => formatMw(row.forecast_generation_mw) },
  ];
  if (showActual) {
    columns.push(
      { key: "actual", header: "Actual MW", align: "right", render: (row) => formatMw(row.actual_generation_mw) },
      { key: "error", header: "Error MW", align: "right", render: (row) => formatSignedMw(displayError(row)) },
    );
  }
  columns.push(
    { key: "published", header: "Published", render: (row) => formatLondonDateTime(row.publish_time) },
    { key: "status", header: "Status", render: (row) => <StatusBadge {...rowStatus(row, showActual)} /> },
  );

  return (
    <div className="forecast-table">
      <DataTable
        columns={columns}
        rows={rows}
        rowKey={(row) => row.start_time}
        rowClassName={(row) => (rowStatus(row, showActual).tone === "matched" ? undefined : "is-missing")}
      />
    </div>
  );
}
