export const primary = {
  10: "#EEF3FF",
  20: "#D9E4FF",
  30: "#B7CBFF",
  40: "#8AABFF",
  50: "#5C86F8",
  60: "#3B6EF6",
  70: "#2F5AD4",
  80: "#2447A8",
  90: "#1C3680",
  100: "#142656",
} as const;

export const accent = {
  10: "#E7FBF6",
  20: "#C4F4E8",
  30: "#8EE8D2",
  40: "#4ED9B8",
  50: "#2EC9A8",
  60: "#14B89A",
  70: "#0E9A82",
  80: "#0C7C69",
  90: "#0A5E50",
  100: "#084439",
} as const;

export const neutral = {
  10: "#FFFFFF",
  20: "#F7F9FC",
  30: "#F2F5F9",
  40: "#E6ECF4",
  50: "#D5DDE8",
  60: "#9AA6B8",
  70: "#6B7689",
  80: "#4E596B",
  90: "#2E3848",
  100: "#1C2434",
} as const;

export const semantic = {
  success: "#15803D",
  successLight: "#DCFCE7",
  warning: "#B45309",
  warningLight: "#FEF3C7",
  danger: "#B42318",
  dangerLight: "#FEE4E2",
  info: "#3B6EF6",
  infoLight: "#EEF3FF",
} as const;

export const chartColors = {
  forecast: accent[60],
  actual: primary[60],
  errorPositive: semantic.warning,
  errorNegative: accent[70],
  grid: neutral[40],
  axis: neutral[70],
} as const;

export const layoutColors = {
  sidebarBackground: "#1C2434",
  sidebarText: neutral[50],
  sidebarActiveBackground: "#2E3848",
  sidebarActiveText: neutral[10],
  pageBackground: "#3B6EF6",
  pageGradient: "linear-gradient(to bottom, #2447A8 0%, #3B6EF6 52%, #8AABFF 100%)",
  surface: neutral[10],
  border: "#E7EDF5",
  textPrimary: neutral[100],
  textSecondary: neutral[70],
  overlay: "rgba(28, 36, 52, 0.28)",
  cloud: "rgba(255, 255, 255, 0.92)",
  cloudSoft: "rgba(255, 255, 255, 0.55)",
  toggleTrack: "#F3F5F8",
  gradientAccent: "linear-gradient(115deg, #3DDCB6 0%, #1BB89A 58%, #149A84 100%)",
  primaryShadow: "0 6px 14px rgba(59, 110, 246, 0.28)",
} as const;

export const theme = {
  primary,
  accent,
  neutral,
  semantic,
  chartColors,
  layoutColors,
} as const;

function assignGroup(target: CSSStyleDeclaration, prefix: string, group: Record<string, string>) {
  for (const [shade, value] of Object.entries(group)) {
    target.setProperty(`--${prefix}-${shade}`, value);
  }
}

export function applyTheme() {
  const style = document.documentElement.style;
  assignGroup(style, "primary", primary);
  assignGroup(style, "accent", accent);
  assignGroup(style, "neutral", neutral);
  assignGroup(style, "semantic", semantic);
  style.setProperty("--color-chart-forecast", chartColors.forecast);
  style.setProperty("--color-chart-actual", chartColors.actual);
  style.setProperty("--color-chart-error-positive", chartColors.errorPositive);
  style.setProperty("--color-chart-error-negative", chartColors.errorNegative);
  style.setProperty("--color-chart-grid", chartColors.grid);
  style.setProperty("--color-chart-axis", chartColors.axis);
  style.setProperty("--color-sidebar-background", layoutColors.sidebarBackground);
  style.setProperty("--color-sidebar-text", layoutColors.sidebarText);
  style.setProperty("--color-sidebar-active", layoutColors.sidebarActiveBackground);
  style.setProperty("--color-sidebar-active-text", layoutColors.sidebarActiveText);
  style.setProperty("--color-page-background", layoutColors.pageBackground);
  style.setProperty("--gradient-page", layoutColors.pageGradient);
  style.setProperty("--color-surface", layoutColors.surface);
  style.setProperty("--color-border", layoutColors.border);
  style.setProperty("--color-text-primary", layoutColors.textPrimary);
  style.setProperty("--color-text-secondary", layoutColors.textSecondary);
  style.setProperty("--color-overlay", layoutColors.overlay);
  style.setProperty("--color-cloud", layoutColors.cloud);
  style.setProperty("--color-cloud-soft", layoutColors.cloudSoft);
  style.setProperty("--color-toggle-track", layoutColors.toggleTrack);
  style.setProperty("--gradient-accent", layoutColors.gradientAccent);
  style.setProperty("--shadow-primary", layoutColors.primaryShadow);
  style.setProperty("--color-success", semantic.success);
  style.setProperty("--color-success-light", semantic.successLight);
  style.setProperty("--color-warning", semantic.warning);
  style.setProperty("--color-warning-light", semantic.warningLight);
  style.setProperty("--color-danger", semantic.danger);
  style.setProperty("--color-danger-light", semantic.dangerLight);
  style.setProperty("--color-info", semantic.info);
  style.setProperty("--color-info-light", semantic.infoLight);
}
