import { queryOptions } from "@tanstack/react-query";
import type { AccuracyQuery, AccuracyResponse } from "../types/accuracy";
import { apiGet } from "./apiClient";

export function fetchAccuracy(query: AccuracyQuery, signal?: AbortSignal): Promise<AccuracyResponse> {
  return apiGet<AccuracyResponse>("/accuracy", query, signal);
}

export function accuracyQueryOptions(deliveryDate: string, decisionTime: string) {
  return queryOptions({
    queryKey: ["accuracy", deliveryDate, decisionTime],
    queryFn: ({ signal }) =>
      fetchAccuracy({ delivery_date: deliveryDate, decision_time: decisionTime }, signal),
  });
}
