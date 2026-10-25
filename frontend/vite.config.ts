
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "https://wind-energy-forecasting-2c1x.onrender.com",
        changeOrigin: true,
      },
    },
  },
});
