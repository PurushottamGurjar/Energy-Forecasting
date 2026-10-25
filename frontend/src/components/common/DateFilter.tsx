import { useState } from "react";
import { DatePicker } from "./DatePicker";
import "./DateFilter.css";

type DateFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
};

export function DateField({ label, value, onChange }: DateFieldProps) {
  const [open, setOpen] = useState(false);

  return (
    <label className="date-filter">
      {label}
      <span className="field-control field-control--date">
        <button type="button" className="date-field__trigger" onClick={() => setOpen(true)}>
          <span>{formatDisplay(value)}</span>
          <CalendarIcon />
        </button>
      </span>
      {open ? <DatePicker value={value} onChange={onChange} onClose={() => setOpen(false)} /> : null}
    </label>
  );
}

type DateFilterProps = {
  value: string;
  onChange: (value: string) => void;
};

export function DateFilter({ value, onChange }: DateFilterProps) {
  return <DateField label="Delivery date" value={value} onChange={onChange} />;
}

function formatDisplay(value: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) {
    return value;
  }
  return `${match[3]}-${match[2]}-${match[1]}`;
}

function CalendarIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 10h18" />
      <path d="M8 3v4" />
      <path d="M16 3v4" />
    </svg>
  );
}
