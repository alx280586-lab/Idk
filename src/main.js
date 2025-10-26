import { Atmosphere } from "./atmo.js";
import { Radar } from "./radar.js";
import { Renderer } from "./renderer.js";
import { Alerts } from "./alerts.js";
import { Analyst } from "./analyst.js";
import { UI } from "./ui.js";

const DEFAULT_SIM_MINUTE_MS = 100;

const state = {
  atmo: Atmosphere.create(Date.now() & 0xffffffff),
  radarCurrent: Radar.create(),
  radarNext: Radar.create(),
  renderer: null,
  alerts: Alerts.create(),
  analyst: Analyst.create(),
  options: {
    clutterFilter: false,
    dealias: false,
    dualPol: true,
    diurnal: true,
    moisture: true,
    showTracks: true,
    showShear: false,
    showAccumulation: false,
    showHailProb: false,
    showPhase: false,
    annotations: false,
    colorBlind: false,
    tornadoFactor: 0.35,
    falseAlarm: 0.05
  },
  clock: {
    timeMinutes: 0,
    running: true,
    playback: 1,
    manual: false,
    targetMinute: 0,
    msPerMinute: DEFAULT_SIM_MINUTE_MS,
    dayLengthMinutes: (DEFAULT_SIM_MINUTE_MS * 1440) / 60000
  },
  overlayCtx: null,
  warningsCtx: null,
  timelineSlider: null,
  simTimeLabel: document.getElementById("sim-time"),
  consoleBody: document.getElementById("console-body"),
  afdLog: document.getElementById("afd-log"),
  capeValue: document.getElementById("cape-value"),
  shearValue: document.getElementById("shear-value"),
  helicityValue: document.getElementById("helicity-value"),
  resetEnvironment: () => {}
};

async function init() {
  const config = await collectInitialConfig();
  const canvas = document.getElementById("radar-canvas");
  state.renderer = Renderer.create(canvas);
  state.overlayCtx = document.getElementById("overlay-canvas").getContext("2d");
  state.warningsCtx = document.createElement("canvas").getContext("2d");
  const overlayCanvas = document.getElementById("overlay-canvas");
  const warningsCanvas = document.createElement("canvas");
  warningsCanvas.width = overlayCanvas.width;
  warningsCanvas.height = overlayCanvas.height;
  warningsCanvas.style.position = "absolute";
  warningsCanvas.style.top = "0";
  warningsCanvas.style.left = "0";
  warningsCanvas.style.width = "100%";
  warningsCanvas.style.height = "100%";
  document.getElementById("warnings-layer").appendChild(warningsCanvas);
  state.warningsCtx = warningsCanvas.getContext("2d");

  state.timelineSlider = document.getElementById("time-slider");
  state.resetEnvironment = resetEnvironment;
  applySimulationConfig(config);
  await applyInitialFastForward(config.fastForwardDays);
  UI.setup(state);
  hideLoading();
  requestAnimationFrame(loop);
}

function applySimulationConfig(config) {
  const { dayLengthMinutes } = config;
  const fallback = state.clock.dayLengthMinutes;
  const minutes = Math.max(0.25, Number.isFinite(dayLengthMinutes) ? dayLengthMinutes : fallback);
  const msPerMinute = (minutes * 60000) / 1440;
  state.clock.msPerMinute = msPerMinute;
  state.clock.dayLengthMinutes = minutes;
  state.clock.timeMinutes = state.atmo.timeMinutes;
  state.timelineSlider.min = 0;
  state.timelineSlider.max = 1440;
  state.timelineSlider.value = state.clock.timeMinutes;
  accumulator = 0;
  lastTimestamp = 0;
}

async function collectInitialConfig() {
  const form = document.getElementById("session-config-form");
  if (!form) {
    return { dayLengthMinutes: state.clock.dayLengthMinutes, fastForwardDays: 0 };
  }
  const submitButton = form.querySelector("button[type=submit]");
  const dayLengthInput = document.getElementById("day-length-input");
  const fastForwardInput = document.getElementById("fast-forward-input");
  const message = document.getElementById("loading-message");
  return new Promise((resolve) => {
    const handleSubmit = (event) => {
      event.preventDefault();
      const dayLengthMinutes = parseFloat(dayLengthInput.value);
      const fastForwardDays = parseFloat(fastForwardInput.value);
      submitButton.disabled = true;
      submitButton.textContent = "Preparing…";
      if (message) {
        message.textContent = "Configuring simulation";
      }
      form.removeEventListener("submit", handleSubmit);
      resolve({
        dayLengthMinutes: Number.isFinite(dayLengthMinutes)
          ? dayLengthMinutes
          : state.clock.dayLengthMinutes,
        fastForwardDays: Math.max(0, Number.isFinite(fastForwardDays) ? fastForwardDays : 0)
      });
    };
    form.addEventListener("submit", handleSubmit);
  });
}

async function applyInitialFastForward(days) {
  const totalMinutes = Math.max(0, Math.floor((Number.isFinite(days) ? days : 0) * 1440));
  if (totalMinutes === 0) {
    Radar.generate(state.radarCurrent, state.atmo, state.options);
    Radar.generate(state.radarNext, state.atmo, state.options);
    state.clock.timeMinutes = state.atmo.timeMinutes;
    state.timelineSlider.value = state.clock.timeMinutes;
    return;
  }
  const message = document.getElementById("loading-message");
  const progress = document.querySelector("#loading-screen .progress");
  if (progress) {
    progress.style.animation = "none";
    progress.style.transform = "scaleX(0)";
  }
  let advanced = 0;
  while (advanced < totalMinutes) {
    const step = Math.min(10, totalMinutes - advanced);
    Atmosphere.update(state.atmo, step, state.options);
    advanced += step;
    if (progress) {
      const pct = advanced / totalMinutes;
      progress.style.transform = `scaleX(${pct.toFixed(3)})`;
    }
    if (message) {
      message.textContent = `Fast-forwarding ${days.toFixed(1)} day${days === 1 ? "" : "s"}… ${Math.round(
        (advanced / totalMinutes) * 100
      )}%`;
    }
    if (advanced < totalMinutes) {
      await new Promise((resolve) => setTimeout(resolve, 0));
    }
  }
  Radar.generate(state.radarCurrent, state.atmo, state.options);
  Radar.generate(state.radarNext, state.atmo, state.options);
  state.clock.timeMinutes = state.atmo.timeMinutes;
  state.timelineSlider.value = state.clock.timeMinutes;
}

function hideLoading() {
  const loading = document.getElementById("loading-screen");
  loading.classList.remove("visible");
}

let lastTimestamp = 0;
let accumulator = 0;

function loop(timestamp) {
  if (!lastTimestamp) lastTimestamp = timestamp;
  const delta = timestamp - lastTimestamp;
  lastTimestamp = timestamp;
  accumulator += delta;

  const minuteStep = state.clock.playback * (delta / state.clock.msPerMinute);
  if (state.clock.manual) {
    state.atmo.timeMinutes = state.clock.targetMinute;
    state.clock.timeMinutes = state.clock.targetMinute;
    state.clock.manual = false;
  } else if (state.clock.running) {
    state.clock.timeMinutes = (state.clock.timeMinutes + minuteStep + 1440) % 1440;
    state.atmo.timeMinutes = state.clock.timeMinutes;
  }

  while (accumulator >= state.clock.msPerMinute) {
    const dtMinutes = state.clock.playback;
    Atmosphere.update(state.atmo, dtMinutes, state.options);
    Radar.generate(state.radarNext, state.atmo, state.options);
    Radar.blend(state.radarCurrent, state.radarNext, 0.25);
    accumulator -= state.clock.msPerMinute;
  }

  const productField = state.radarCurrent[state.renderer.currentProduct];
  Renderer.uploadField(state.renderer, productField);
  Renderer.resize(state.renderer);
  resizeOverlay();
  Renderer.render(state.renderer, { time: timestamp * 0.001 });

  renderStormTracks();
  updateWarnings(timestamp * 0.001);
  updateUI(timestamp * 0.001);

  requestAnimationFrame(loop);
}

function resizeOverlay() {
  const overlay = state.overlayCtx.canvas;
  const warningsCanvas = state.warningsCtx.canvas;
  const width = overlay.clientWidth;
  const height = overlay.clientHeight;
  if (overlay.width !== width || overlay.height !== height) {
    overlay.width = width;
    overlay.height = height;
  }
  if (warningsCanvas.width !== width || warningsCanvas.height !== height) {
    warningsCanvas.width = width;
    warningsCanvas.height = height;
  }
}

function renderStormTracks() {
  const ctx = state.overlayCtx;
  const canvas = ctx.canvas;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!state.options.showTracks) return;
  ctx.save();
  ctx.strokeStyle = "rgba(255,255,255,0.4)";
  ctx.lineWidth = 1;
  for (const storm of state.atmo.storms) {
    ctx.beginPath();
    storm.track.forEach((step, index) => {
      const p = project(step.x, step.y, canvas.width, canvas.height);
      if (index === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    });
    ctx.stroke();
    const current = project(storm.x, storm.y, canvas.width, canvas.height);
    ctx.fillStyle = storm.debrisStrength > 0.6 ? "rgba(255,80,80,0.9)" : "rgba(80,160,255,0.8)";
    ctx.beginPath();
    ctx.arc(current.x, current.y, 4 + storm.debrisStrength * 6, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

function updateWarnings(timeSeconds) {
  Alerts.update(state.alerts, state.radarCurrent, state.atmo.storms, state.atmo.timeMinutes, state.options);
  const canvas = state.warningsCtx.canvas;
  canvas.width = state.overlayCtx.canvas.width;
  canvas.height = state.overlayCtx.canvas.height;
  Alerts.render(
    state.warningsCtx,
    state.alerts.active,
    timeSeconds,
    (x, y) => project(x, y, canvas.width, canvas.height)
  );
  renderWarningLog();
}

function renderWarningLog() {
  const container = state.consoleBody;
  container.innerHTML = "";
  state.alerts.active.forEach((warning) => {
    const div = document.createElement("div");
    div.className = "entry";
    div.textContent = `${formatTime(state.atmo.timeMinutes)}Z ${warning.headline}`;
    container.appendChild(div);
  });
}

function updateUI(timeSeconds) {
  state.simTimeLabel.textContent = `SIM TIME ${formatTime(state.atmo.timeMinutes)} UTC`;
  state.timelineSlider.value = state.atmo.timeMinutes;
  const metrics = computeBulkMetrics();
  state.capeValue.textContent = `${Math.round(metrics.cape)} J/kg`;
  state.shearValue.textContent = `${Math.round(metrics.shear)} kt`;
  state.helicityValue.textContent = `${Math.round(metrics.helicity)} m²/s²`;
  const hour = (state.atmo.timeMinutes / 60) % 24;
  const night = hour < 6 || hour > 19;
  state.renderer.nightFactor = night ? 1 : Math.max(0, 1 - Math.abs(hour - 12) / 6);
  Analyst.update(state.analyst, state.atmo.storms, state.atmo.timeMinutes, state.afdLog);
}

function computeBulkMetrics() {
  const storms = state.atmo.storms;
  if (!storms.length) return { cape: 0, shear: 0, helicity: 0 };
  const cape = storms.reduce((sum, storm) => sum + storm.updraft * 80, 0) / storms.length;
  const shear = storms.reduce((sum, storm) => sum + storm.rotation * 50, 0) / storms.length;
  const helicity = storms.reduce((sum, storm) => sum + storm.rotation * storm.intensity, 0) / storms.length;
  return { cape, shear, helicity };
}

function project(x, y, width, height) {
  const u = x / Radar.GRID_SIZE;
  const v = y / Radar.GRID_SIZE;
  return {
    x: u * width,
    y: v * height
  };
}

function formatTime(minutes) {
  const h = Math.floor(minutes / 60) % 24;
  const m = Math.floor(minutes % 60);
  return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}`;
}

function resetEnvironment() {
  state.atmo = Atmosphere.create(Math.floor(Math.random() * 1e9));
  state.radarCurrent = Radar.create();
  state.radarNext = Radar.create();
  state.alerts = Alerts.create();
  state.analyst = Analyst.create();
  state.clock.timeMinutes = 0;
  state.clock.running = false;
  state.timelineSlider.value = 0;
  state.consoleBody.innerHTML = "";
  state.afdLog.innerHTML = "";
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init, { once: true });
} else {
  init();
}
