import { Radar } from "./radar.js";

const WARNING_TYPES = {
  tornado: { color: "rgba(220,50,50,0.35)", border: "#ff2f2f", label: "TOR" },
  tornadoPds: { color: "rgba(255,0,0,0.45)", border: "#ff00aa", label: "TOR PDS" },
  tornadoEmergency: { color: "rgba(180,0,0,0.6)", border: "#ffdd00", label: "TOR EMER" },
  severe: { color: "rgba(255,220,0,0.28)", border: "#ffdd55", label: "SVR" },
  severePds: { color: "rgba(255,150,0,0.35)", border: "#ff8c00", label: "SVR PDS" },
  flashFlood: { color: "rgba(20,140,60,0.3)", border: "#44ff88", label: "FFW" },
  flashFloodPds: { color: "rgba(20,200,80,0.4)", border: "#00ff55", label: "PDS FFW" },
  winter: { color: "rgba(120,120,255,0.3)", border: "#ccd5ff", label: "WINTER" },
  snowSquall: { color: "rgba(220,220,255,0.35)", border: "#ffffff", label: "SQW" }
};

const METRO_AREAS = [
  { name: "OKC", x: 0.46, y: 0.56 },
  { name: "DAL", x: 0.45, y: 0.7 },
  { name: "TUL", x: 0.5, y: 0.52 }
];

export function createAlerts() {
  return {
    active: [],
    history: []
  };
}

export function updateAlerts(alerts, radarState, storms, timeMinutes, options) {
  const newWarnings = [];
  for (const storm of storms) {
    const poly = stormToPolygon(storm);
    const attributes = sampleAttributes(storm, radarState);
    evaluateWarnings(storm, attributes, poly, newWarnings, timeMinutes, options);
  }

  mergeWarnings(alerts, newWarnings, timeMinutes);
  expireWarnings(alerts, timeMinutes);
  return alerts;
}

function stormToPolygon(storm) {
  const radius = 40 + storm.intensity * 0.5;
  const verts = [];
  for (let i = 0; i < 6; i++) {
    const angle = (i / 6) * Math.PI * 2;
    verts.push({
      x: storm.x + Math.cos(angle) * radius,
      y: storm.y + Math.sin(angle) * radius
    });
  }
  return verts;
}

function sampleAttributes(storm, radarState) {
  const { reflectivity, velocity, cc, zdr } = radarState;
  const radius = Math.max(20, Math.min(80, storm.intensity));
  let maxRefl = 0;
  let minCC = 1;
  let zdrMean = 0;
  let zdrSamples = 0;
  let velDiff = 0;
  for (let y = -radius; y <= radius; y += 4) {
    const gy = Math.floor(storm.y + y);
    if (gy < 0 || gy >= Radar.GRID_SIZE) continue;
    for (let x = -radius; x <= radius; x += 4) {
      const gx = Math.floor(storm.x + x);
      if (gx < 0 || gx >= Radar.GRID_SIZE) continue;
      const idx = gy * Radar.GRID_SIZE + gx;
      const dist = Math.hypot(x, y);
      if (dist > radius) continue;
      maxRefl = Math.max(maxRefl, reflectivity[idx]);
      minCC = Math.min(minCC, cc[idx]);
      zdrMean += zdr[idx];
      zdrSamples++;
      const pairIdx = gy * Radar.GRID_SIZE + Math.max(0, Math.min(Radar.GRID_SIZE - 1, Math.floor(storm.x - x)));
      velDiff = Math.max(velDiff, Math.abs(velocity[idx] - velocity[pairIdx]));
    }
  }
  zdrMean = zdrSamples > 0 ? zdrMean / zdrSamples : 0.5;
  return { maxRefl, minCC, zdrMean, velDiff };
}

function evaluateWarnings(storm, attrs, polygon, warnings, timeMinutes, options) {
  const { maxRefl, minCC, velDiff } = attrs;
  const hasCouplet = velDiff > 80;
  const hailSignal = maxRefl > 65 && attrs.zdrMean < 1;
  const baseWarning = {
    stormId: storm.id,
    polygon,
    issue: timeMinutes,
    expires: timeMinutes + 30,
    headline: "",
    type: null,
    severity: 1,
    meta: {}
  };

  if (hasCouplet && minCC < 0.8 && Math.random() > options.falseAlarm * 0.25) {
    const warning = { ...baseWarning };
    warning.type = "tornado";
    warning.headline = `TORNADO WARNING – ${Math.round(velDiff)} KT G2G`;
    if (maxRefl > 70 && attrs.zdrMean < 0) {
      warning.type = "tornadoPds";
      warning.headline = `PDS TORNADO WARNING – ${Math.round(velDiff)} KT COUPLET`;
    }
    if (isMetroIntersect(polygon)) {
      warning.type = "tornadoEmergency";
      warning.headline = "TORNADO EMERGENCY – TAKE COVER NOW";
    }
    warnings.push(warning);
  }

  if (maxRefl > 60 || hailSignal || Math.random() < options.falseAlarm) {
    const warning = { ...baseWarning };
    warning.type = hailSignal ? "severePds" : "severe";
    warning.headline = hailSignal
      ? "PDS SEVERE THUNDERSTORM – VERY LARGE HAIL"
      : "SEVERE THUNDERSTORM – 60 KT WINDS";
    warning.expires = timeMinutes + 45;
    warnings.push(warning);
  }

  if (storm.phase === "tropical" && maxRefl > 45 && Math.random() > options.falseAlarm * 0.5) {
    const warning = { ...baseWarning };
    warning.type = "flashFlood";
    warning.headline = "FLASH FLOOD WARNING – TRAINING RAINBANDS";
    warning.expires = timeMinutes + 60;
    warnings.push(warning);
  }

  if (storm.phase === "decay" && attrs.zdrMean < 0.5 && minCC > 0.95) {
    const warning = { ...baseWarning };
    warning.type = "winter";
    warning.headline = "WINTER WEATHER ADVISORY – MIXED PRECIP";
    warning.expires = timeMinutes + 90;
    warnings.push(warning);
  }
}

function mergeWarnings(alerts, warnings, timeMinutes) {
  for (const warn of warnings) {
    const existing = alerts.active.find((w) => w.stormId === warn.stormId && w.type === warn.type);
    if (existing) {
      existing.polygon = warn.polygon;
      existing.expires = Math.max(existing.expires, warn.expires);
      existing.headline = warn.headline;
    } else {
      const meta = WARNING_TYPES[warn.type] || WARNING_TYPES.severe;
      const entry = {
        ...warn,
        ...meta,
        id: `${warn.type}-${warn.stormId}-${Math.round(timeMinutes)}`
      };
      alerts.active.push(entry);
      alerts.history.push(entry);
    }
  }
}

function expireWarnings(alerts, timeMinutes) {
  alerts.active = alerts.active.filter((warning) => {
    if (warning.expires < timeMinutes) {
      warning.fading = warning.fading ?? timeMinutes + 3;
    }
    return warning.fading == null || warning.fading > timeMinutes;
  });
}

function isMetroIntersect(polygon) {
  for (const metro of METRO_AREAS) {
    const px = metro.x * Radar.GRID_SIZE;
    const py = metro.y * Radar.GRID_SIZE;
    if (pointInPolygon(px, py, polygon)) return true;
  }
  return false;
}

function pointInPolygon(x, y, polygon) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i].x;
    const yi = polygon[i].y;
    const xj = polygon[j].x;
    const yj = polygon[j].y;
    const intersect = yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi + 1e-6) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}

export function renderWarnings(ctx, warnings, alphaPulse, projection) {
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  for (const warning of warnings) {
    if (!warning.polygon) continue;
    ctx.save();
    ctx.beginPath();
    warning.polygon.forEach((p, index) => {
      const screen = projection(p.x, p.y);
      if (index === 0) ctx.moveTo(screen.x, screen.y);
      else ctx.lineTo(screen.x, screen.y);
    });
    ctx.closePath();
    ctx.fillStyle = warning.color;
    ctx.globalAlpha = 0.7 + 0.3 * Math.sin(alphaPulse * Math.PI * 2);
    ctx.fill();
    ctx.lineWidth = 2 + 1.5 * Math.sin(alphaPulse * 4 * Math.PI);
    ctx.strokeStyle = warning.border;
    ctx.stroke();

    const centroid = warning.polygon.reduce(
      (acc, p) => {
        acc.x += p.x;
        acc.y += p.y;
        return acc;
      },
      { x: 0, y: 0 }
    );
    centroid.x /= warning.polygon.length;
    centroid.y /= warning.polygon.length;
    const labelPos = projection(centroid.x, centroid.y);
    ctx.fillStyle = "rgba(0,0,0,0.6)";
    ctx.fillRect(labelPos.x - 24, labelPos.y - 12, 48, 18);
    ctx.fillStyle = "#fff";
    ctx.font = "700 10px 'Segoe UI', sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(warning.label, labelPos.x, labelPos.y - 1);
    ctx.restore();
  }
}

export const Alerts = {
  create: createAlerts,
  update: updateAlerts,
  render: renderWarnings
};
