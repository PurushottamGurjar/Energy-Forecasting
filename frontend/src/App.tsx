import { AppProvider } from "./Provider/provider";
import { DashboardPage } from "./pages/DashboardPage";
import "./App.css";

export function App() {
  return (
    <AppProvider>
      <DashboardPage />
    </AppProvider>
  );
}
