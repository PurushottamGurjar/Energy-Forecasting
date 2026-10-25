import { queryOptions } from "@tanstack/react-query";
import type { ForecastQuery, ForecastResponse } from "../types/forecast";
import { apiGet } from "./apiClient";

export function fetchForecast(query: ForecastQuery, signal?: AbortSignal): Promise<ForecastResponse> {
  return apiGet<ForecastResponse>("/forecasts", query, signal);
}

export function forecastQueryOptions(deliveryDate: string, decisionTime: string, includeActuals: boolean) {
  return queryOptions({
    queryKey: ["forecast", deliveryDate, decisionTime, includeActuals],
    queryFn: ({ signal }) =>
      fetchForecast(
        { delivery_date: deliveryDate, decision_time: decisionTime, include_actuals: includeActuals },
        signal,
      ),
  });
}
