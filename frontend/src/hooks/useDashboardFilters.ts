import { useState } from "react";
import {
  DEFAULT_DECISION_CLOCK,
  DEFAULT_DECISION_DATE,
  DEFAULT_DELIVERY_DATE,
  isJanuary2026,
  londonLocalToUtcIso,
} from "../utils/date";

export type AnalysisView = "forecast" | "accuracy";

type AppliedFilters = {
  deliveryDate: string;
  decisionDate: string;
  decisionClock: string;
  showActual: boolean;
  requestId: number;
};

export function useDashboardFilters() {
  const [deliveryDate, setDeliveryDate] = useState(DEFAULT_DELIVERY_DATE);
  const [decisionDate, setDecisionDate] = useState(DEFAULT_DECISION_DATE);
  const [decisionClock, setDecisionClock] = useState(DEFAULT_DECISION_CLOCK);
  const [showActual, setShowActual] = useState(true);
  const [view, setView] = useState<AnalysisView>("forecast");
  const [applied, setApplied] = useState<AppliedFilters>({
    deliveryDate: DEFAULT_DELIVERY_DATE,
    decisionDate: DEFAULT_DECISION_DATE,
    decisionClock: DEFAULT_DECISION_CLOCK,
    showActual: true,
    requestId: 0,
  });

  function generate() {
    setApplied((current) => ({
      deliveryDate,
      decisionDate,
      decisionClock,
      showActual,
      requestId: current.requestId + 1,
    }));
  }

  return {
    deliveryDate,
    decisionDate,
    decisionClock,
    showActual,
    view,
    setDeliveryDate,
    setDecisionDate,
    setDecisionClock,
    setShowActual,
    setView,
    generate,
    appliedDeliveryDate: applied.deliveryDate,
    appliedDecisionTime: londonLocalToUtcIso(applied.decisionDate, applied.decisionClock),
    appliedShowActual: applied.showActual,
    appliedRequestId: applied.requestId,
    deliveryDateValid: isJanuary2026(applied.deliveryDate),
  };
}
