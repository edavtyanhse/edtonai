import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { getUserId } from "./lib/auth";

createRoot(document.getElementById("root")!).render(<App />);

// Ensure a user id exists as soon as the frontend mounts.
getUserId();
