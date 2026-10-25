import { DateFilter } from "../common/DateFilter";
import { DecisionCutoffFilter } from "../common/DecisionCutoffFilter";
import "./Filter.css";

type FilterProps = {
  deliveryDate: string;
  decisionDate: string;
  decisionClock: string;
  showActual: boolean;
  onDeliveryDateChange: (value: string) => void;
  onDecisionDateChange: (value: string) => void;
  onDecisionClockChange: (value: string) => void;
  onShowActualChange: (value: boolean) => void;
  onGenerate: () => void;
};

export function Filter(props: FilterProps) {
  return (
    <form
      className="filter-bar"
      onSubmit={(event) => {
        event.preventDefault();
        props.onGenerate();
      }}
    >
      <div className="filter-bar__fields">
        <DateFilter value={props.deliveryDate} onChange={props.onDeliveryDateChange} />
        <DecisionCutoffFilter
          date={props.decisionDate}
          time={props.decisionClock}
          onDateChange={props.onDecisionDateChange}
          onTimeChange={props.onDecisionClockChange}
        />
        <label className="filter-bar__check">
          <input
            type="checkbox"
            checked={props.showActual}
            onChange={(event) => props.onShowActualChange(event.target.checked)}
          />
          Show actual
        </label>
      </div>
      <button className="filter-bar__generate" type="submit">
        <SearchIcon />
        Generate Analysis
      </button>
    </form>
  );
}

function SearchIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="11" cy="11" r="7" />
      <path d="M20 20l-3.5-3.5" />
    </svg>
  );
}
