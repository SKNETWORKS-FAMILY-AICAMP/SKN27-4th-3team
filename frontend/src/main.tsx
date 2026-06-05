import React from "react";
import { createRoot } from "react-dom/client";
import { AppRouter } from "./app/router/AppRouter";
import "./shared/ui/global.css";

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <AppRouter />
  </React.StrictMode>,
);

