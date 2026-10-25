export type AccuracyPeriod = {
  start_time: string;
  publish_time: string | null;
  forecast_generation_mw: number | null;
  actual_generation_mw: number | null;
  error_mw: number | null;
  absolute_error_mw: number | null;
};

export type AccuracyMetrics = {
  mae_mw: number | null;
  rmse_mw: number | null;
  bias_mw: number | null;
  mape_percent: number | null;
  mape_observations: number;
};

export type AccuracyCoverage = {
  expected_periods: number;
  matched_periods: number;
  missing_forecast_periods: number;
  missing_actual_periods: number;
};

export type AccuracyResponse = {
  delivery_date: string;
  decision_time: string;
  unit: string;
  coverage: AccuracyCoverage;
  metrics: AccuracyMetrics;
  data: AccuracyPeriod[];
};

export type AccuracyQuery = {
  delivery_date: string;
  decision_time: string;
};
