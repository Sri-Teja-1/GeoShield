import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles/tailwind.css";
import "./styles/globals.css";

// Phase 0 scaffold: minimal mount point so `npm run dev` renders and `tsc`
// passes. App.tsx (router), pages, and components are built starting in Phase 6.
const container = document.getElementById("root");
if (!container) {
  throw new Error("Root element #root not found");
}

createRoot(container).render(
  <StrictMode>
    <main className="grid min-h-screen place-items-center bg-surface px-xl text-center text-on-surface">
      <div>
        <h1 className="font-display text-display-sm text-on-surface">GeoShield</h1>
        <p className="mt-md font-body text-body-md text-on-surface-variant">
          Scaffold ready. Build the workspace from Phase 6 onward.
        </p>
      </div>
    </main>
  </StrictMode>,
);
