import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "../styles.css";
import "./explorer.css";
import { Shell } from "./Shell";

const root = document.getElementById("root");
if (!root) throw new Error("explorer.html has no #root");

// A marker for the browser check (the content security policy proof): set once the explorer has mounted.
document.documentElement.dataset["mounted"] = "yes";

createRoot(root).render(
  <StrictMode>
    <Shell />
  </StrictMode>,
);
