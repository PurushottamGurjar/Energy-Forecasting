import { useEffect } from "react";
import { createPortal } from "react-dom";
import "./DatePicker.css";

const YEAR = 2026;
const MONTH = 0;
const WEEKDAYS = ["S", "M", "T", "W", "T", "F", "S"];

type DatePickerProps = {
  value: string;
  onChange: (value: string) => void;
  onClose: () => void;
};

export function DatePicker({ value, onChange, onClose }: DatePickerProps) {
  const selectedDay = selectedJanuaryDay(value);
  const cells = januaryCells();

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return createPortal(
    <div className="date-modal" role="presentation" onMouseDown={onClose}>
      <div
        className="date-modal__dialog"
        role="dialog"
        aria-modal="true"
        aria-label="Select a date"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <h2>Select a date</h2>
        <p className="date-modal__month">January 2026</p>
        <div className="date-modal__week" aria-hidden="true">
          {WEEKDAYS.map((day, index) => (
            <span key={`${day}-${index}`}>{day}</span>
          ))}
        </div>
        <div className="date-modal__grid">
          {cells.map((cell) =>
            cell.day === null ? (
              <span key={cell.key} className="date-modal__outside">
                {cell.label}
              </span>
            ) : (
              <button
                key={cell.key}
                type="button"
                className={cell.day === selectedDay ? "is-selected" : undefined}
                onClick={() => {
                  onChange(januaryIso(cell.day as number));
                  onClose();
                }}
              >
                {cell.day}
              </button>
            ),
          )}
        </div>
      </div>
    </div>,
    document.body,
  );
}

function januaryIso(day: number): string {
  return `${YEAR}-01-${String(day).padStart(2, "0")}`;
}

function selectedJanuaryDay(value: string): number | null {
  const match = /^2026-01-(\d{2})$/.exec(value);
  if (!match) {
    return null;
  }
  const day = Number(match[1]);
  return day >= 1 && day <= 31 ? day : null;
}

function januaryCells(): Array<{ key: string; day: number | null; label: number }> {
  const firstWeekday = new Date(YEAR, MONTH, 1).getDay();
  const cells: Array<{ key: string; day: number | null; label: number }> = [];
  for (let index = 0; index < firstWeekday; index += 1) {
    cells.push({ key: `lead-${index}`, day: null, label: 31 - firstWeekday + index + 1 });
  }
  for (let day = 1; day <= 31; day += 1) {
    cells.push({ key: `day-${day}`, day, label: day });
  }
  const trailing = (7 - (cells.length % 7)) % 7;
  for (let index = 1; index <= trailing; index += 1) {
    cells.push({ key: `tail-${index}`, day: null, label: index });
  }
  return cells;
}
