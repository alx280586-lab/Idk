import { Renderer } from "./renderer.js";
import { getLegendRange } from "./colorTables.js";

export function setupUI(state) {
  const productSelect = document.getElementById("product-select");
  productSelect.addEventListener("change", (event) => {
    const product = event.target.value;
    state.renderer.currentProduct = product;
    Renderer.updateRamp(state.renderer, product);
    const legend = getLegendRange(product);
    document.querySelector("#legend .legend-title").textContent = legend.units;
    document.getElementById("product-label").textContent = product.toUpperCase();
  });

  const toggles = {
    "clutter-toggle": "clutterFilter",
    "dealias-toggle": "dealias",
    "dualpol-toggle": "dualPol",
    "diurnal-toggle": "diurnal",
    "moisture-toggle": "moisture",
    "tracks-toggle": "showTracks",
    "shear-toggle": "showShear",
    "accumulation-toggle": "showAccumulation",
    "hailprob-toggle": "showHailProb",
    "phase-toggle": "showPhase",
    "education-toggle": "annotations",
    "colorblind-toggle": "colorBlind"
  };
  for (const [id, key] of Object.entries(toggles)) {
    const el = document.getElementById(id);
    if (!el) continue;
    state.options[key] = el.checked;
    el.addEventListener("change", () => {
      state.options[key] = el.checked;
      if (key === "colorBlind") {
        state.renderer.colorBlindMode = el.checked;
      }
    });
  }

  const sliderMap = {
    "brightness-slider": (value) => (state.renderer.brightness = parseFloat(value)),
    "contrast-slider": (value) => (state.renderer.contrast = parseFloat(value)),
    "beam-slider": (value) => (state.renderer.beamWidth = parseFloat(value)),
    "legend-bright": (value) => (state.renderer.brightness = parseFloat(value)),
    "legend-gamma": (value) => (state.renderer.gamma = parseFloat(value)),
    "tornado-slider": (value) => (state.options.tornadoFactor = parseFloat(value)),
    "falsealarm-slider": (value) => (state.options.falseAlarm = parseFloat(value))
  };
  for (const [id, handler] of Object.entries(sliderMap)) {
    const el = document.getElementById(id);
    if (!el) continue;
    handler(el.value);
    el.addEventListener("input", () => handler(el.value));
  }

  state.renderer.colorBlindMode = state.options.colorBlind;

  const resetBtn = document.getElementById("reset-env");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => state.resetEnvironment());
  }

  setupDrawer();
  setupTimeline(state);
  setupConsole(state);
  setupKeyboardShortcuts(productSelect);
}

function setupDrawer() {
  const drawer = document.getElementById("control-drawer");
  const toggle = document.getElementById("drawer-toggle");
  toggle.addEventListener("click", () => {
    drawer.classList.toggle("collapsed");
  });
  const tabButtons = drawer.querySelectorAll(".drawer-tabs button");
  const panels = drawer.querySelectorAll(".drawer-panel");
  tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      tabButtons.forEach((b) => b.classList.remove("active"));
      panels.forEach((p) => p.classList.remove("active"));
      button.classList.add("active");
      drawer.querySelector(`.drawer-panel[data-panel="${button.dataset.tab}"]`).classList.add("active");
    });
  });
}

function setupTimeline(state) {
  const slider = document.getElementById("time-slider");
  const playBtn = document.getElementById("play-btn");
  const pauseBtn = document.getElementById("pause-btn");
  const rewindBtn = document.getElementById("rewind-btn");
  const ffBtn = document.getElementById("ff-btn");
  const labels = document.getElementById("time-labels");
  labels.innerHTML = "";
  for (let hour = 0; hour <= 24; hour += 3) {
    const span = document.createElement("span");
    span.textContent = `${hour.toString().padStart(2, "0")}:00`;
    labels.appendChild(span);
  }

  playBtn.addEventListener("click", () => {
    state.clock.playback = 1;
    state.clock.running = true;
    playBtn.classList.add("hidden");
    pauseBtn.classList.remove("hidden");
  });
  pauseBtn.addEventListener("click", () => {
    state.clock.running = false;
    playBtn.classList.remove("hidden");
    pauseBtn.classList.add("hidden");
  });
  rewindBtn.addEventListener("click", () => {
    state.clock.playback = -4;
    state.clock.running = true;
    playBtn.classList.add("hidden");
    pauseBtn.classList.remove("hidden");
  });
  ffBtn.addEventListener("click", () => {
    state.clock.playback = 6;
    state.clock.running = true;
    playBtn.classList.add("hidden");
    pauseBtn.classList.remove("hidden");
  });

  slider.addEventListener("input", () => {
    const minute = parseFloat(slider.value);
    state.clock.manual = true;
    state.clock.targetMinute = minute;
  });
}

function setupConsole(state) {
  const toggleButton = document.getElementById("toggle-console");
  const consoleBody = document.getElementById("console-body");
  const exportButton = document.getElementById("export-log");
  toggleButton.addEventListener("click", () => {
    const collapsed = consoleBody.style.display === "none";
    consoleBody.style.display = collapsed ? "flex" : "none";
    toggleButton.textContent = collapsed ? "−" : "+";
  });
  exportButton.addEventListener("click", () => {
    const rows = state.alerts.history.map((entry) =>
      [entry.issue.toFixed(1), entry.type, entry.headline, entry.id].join(",")
    );
    const csv = ["time,type,headline,id", ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "synthetic-warnings.csv";
    a.click();
    URL.revokeObjectURL(url);
  });
}

function setupKeyboardShortcuts(selectEl) {
  const keyMap = {
    r: "reflectivity",
    v: "velocity",
    c: "cc",
    z: "zdr",
    k: "kdp"
  };
  window.addEventListener("keydown", (event) => {
    if (event.target.tagName === "INPUT" || event.target.tagName === "SELECT") return;
    if (event.shiftKey) {
      // TODO: implement dual-pane mode
      return;
    }
    const key = event.key.toLowerCase();
    if (keyMap[key]) {
      selectEl.value = keyMap[key];
      selectEl.dispatchEvent(new Event("change"));
    }
  });
}

export const UI = {
  setup: setupUI
};
