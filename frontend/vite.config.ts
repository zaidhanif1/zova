import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(
{
    plugins: [react()],
    server: {
        port: 5173,
        strictPort: true,
        // The browser calls Vite; Vite forwards this path to FastAPI.
        proxy: { "/itinerary": "http://127.0.0.1:8000" },
    },
});
