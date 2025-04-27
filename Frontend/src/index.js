import React from "react";
import { createRoot } from "react-dom/client";
import BrainTumorDetection from "./brain-tumor-detection";

const container = document.getElementById("root");
const root = createRoot(container);
root.render(<BrainTumorDetection />);
