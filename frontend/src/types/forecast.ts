export type ForecastPeriod = {
  start_time: string;
  publish_time: string | null;
  forecast_generation_mw: number | null;
  actual_generation_mw: number | null;
};

export type ForecastSummary = {
  periods_expected: number;
  periods_with_forecast: number;
  missing_forecast_periods: number;
  average_forecast_mw: number | null;
};

export type ForecastResponse = {
  delivery_date: string;
  decision_time: string;
  timezone: string;
  unit: string;
  summary: ForecastSummary;
  data: ForecastPeriod[];
};

export type ForecastQuery = {
  delivery_date: string;
  decision_time: string;
  include_actuals?: boolean;
};
