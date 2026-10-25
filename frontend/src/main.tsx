import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { applyTheme } from "./styles/theme";
import { applyTokens } from "./styles/tokens";
import "./styles/globals.css";

applyTokens();
applyTheme();

const root = document.getElementById("root");
if (!root) {
  throw new Error("Root element was not found");
}

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
