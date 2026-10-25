import { DateField } from "./DateFilter";
import "./DecisionCutoffFilter.css";

type DecisionCutoffFilterProps = {
  date: string;
  time: string;
  onDateChange: (value: string) => void;
  onTimeChange: (value: string) => void;
};

export function DecisionCutoffFilter({ date, time, onDateChange, onTimeChange }: DecisionCutoffFilterProps) {
  return (
    <fieldset className="cutoff-filter">
      <legend>Decision cutoff, Europe/London</legend>
      <DateField label="Date" value={date} onChange={onDateChange} />
      <label>
        Time
        <span className="field-control field-control--time">
          <ClockIcon />
          <input type="time" value={time} onChange={(event) => onTimeChange(event.target.value)} />
        </span>
      </label>
    </fieldset>
  );
}

function ClockIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="8" />
      <path d="M12 8v5l3 2" />
    </svg>
  );
}
