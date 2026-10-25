import "./Sky.css";

export function Sky() {
  return (
    <div className="sky" aria-hidden="true">
      <Cloud className="sky__cloud sky__cloud--one" />
      <Cloud className="sky__cloud sky__cloud--two sky__cloud--dark" />
      <Cloud className="sky__cloud sky__cloud--three" />
      <Cloud className="sky__cloud sky__cloud--four" />
      <Bolt className="sky__bolt sky__bolt--one" />
      <Bolt className="sky__bolt sky__bolt--two" />
      <Bolt className="sky__bolt sky__bolt--three" />
      <Bolt className="sky__bolt sky__bolt--four" />
    </div>
  );
}

function Cloud({ className }: { className: string }) {
  return (
    <svg className={className} viewBox="0 0 160 70" fill="none">
      <path
        fill="#ffffff"
        d="M46 54h74c14 0 24-9 24-21s-10-21-24-21c-2-10-12-16-23-16-9 0-17 5-20 12C48 6 38 12 36 22c-12 1-20 10-20 21 0 12 10 21 22 21h8Z"
      />
    </svg>
  );
}

function Bolt({ className }: { className: string }) {
  return (
    <svg className={className} viewBox="0 0 36 64" fill="none">
      <path fill="#FFE14A" d="M22 0 4 36h12L10 64 32 26H18L22 0Z" />
    </svg>
  );
}
