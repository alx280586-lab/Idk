const TIME_WINDOWS = [
  { label: "0-24h", hours: [0, 24] },
  { label: "24-48h", hours: [24, 48] },
  { label: "48-72h", hours: [48, 72] }
];

const RISK_LEVELS = [
  { threshold: 60, color: "#a855f7", label: "Extreme" },
  { threshold: 45, color: "#db2777", label: "High" },
  { threshold: 30, color: "#b91c1c", label: "Moderate" },
  { threshold: 15, color: "#ef4444", label: "Enhanced" },
  { threshold: 10, color: "#f97316", label: "Slight" },
  { threshold: 5, color: "#facc15", label: "Slight" },
  { threshold: 2, color: "#4ade80", label: "Marginal" }
];

function formatLatitude(lat) {
  return `${Math.abs(lat).toFixed(1)}°${lat >= 0 ? "N" : "S"}`;
}

function formatLongitude(lon) {
  return `${Math.abs(lon).toFixed(1)}°${lon >= 0 ? "E" : "W"}`;
}

const map = L.map("map", {
  zoomControl: false,
  minZoom: 3,
  maxZoom: 10
}).setView([37.5, -97], 4.2);

L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
  attribution:
    "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors &copy; <a href='https://carto.com/attributions'>CARTO</a>",
  subdomains: "abcd"
}).addTo(map);

L.control.zoom({ position: "bottomright" }).addTo(map);

const probabilityLayer = L.geoJSON([], {
  style: feature => {
    const opacity = Math.min(0.75, 0.25 + feature.properties.probability / 120);
    return {
      color: feature.properties.color,
      weight: 0.8,
      fillColor: feature.properties.color,
      fillOpacity: opacity,
      opacity: 0.8,
      className: "probability-polygon"
    };
  },
  onEachFeature: (feature, layer) => {
    const { probability, riskLabel, label, centroid, influences } = feature.properties;

    layer.bindTooltip(
      `<strong>${probability}% Tornado Probability</strong><br/><span>${riskLabel} Risk</span>`,
      { sticky: true }
    );

    layer.on("mouseover", () => {
      layer.setStyle({ weight: 1.5, fillOpacity: 0.85 });
      updateInfoPanel({ probability, riskLabel, label, centroid, influences });
    });

    layer.on("mouseout", () => {
      probabilityLayer.resetStyle(layer);
    });

    layer.on("click", () => {
      L.popup()
        .setLatLng([centroid.lat, centroid.lon])
        .setContent(
          `<div class="popup"><h4>${riskLabel} Risk</h4><p><strong>${probability}%</strong> probability<br/>Forecast window: ${label}</p></div>`
        )
        .openOn(map);
    });
  }
}).addTo(map);

let activeForecast = [];
let autoRefreshHandle;

const timeRange = document.getElementById("time-range");
const timeText = document.getElementById("time-text");
const statusFeed = document.getElementById("status-feed");
const generateBtn = document.getElementById("generate-btn");

function getRiskLevel(probability) {
  for (const level of RISK_LEVELS) {
    if (probability >= level.threshold) {
      return level;
    }
  }
  return null;
}

function buildPolygon(lat, lon, latStep, lonStep) {
  return {
    type: "Polygon",
    coordinates: [
      [
        [lon, lat],
        [lon + lonStep, lat],
        [lon + lonStep, lat + latStep],
        [lon, lat + latStep],
        [lon, lat]
      ]
    ]
  };
}

function createStormSeeds(timeIndex) {
  const seedCount = 4 + Math.floor(Math.random() * 3);
  const seeds = [];
  for (let i = 0; i < seedCount; i++) {
    const lat = 26 + Math.random() * 22;
    const lon = -120 + Math.random() * 50;
    const intensity = 0.35 + Math.random() * 0.6;
    const latScale = 3 + Math.random() * 4;
    const lonScale = 3 + Math.random() * 6;
    const shearBoost = Math.random() * 0.2;
    const gulfMoisture = Math.max(0, 1 - (lat - 28) / 10) * 0.15;
    seeds.push({ lat, lon, intensity, latScale, lonScale, shearBoost, gulfMoisture });
  }

  // Slightly favor the central plains as a default corridor
  seeds.push({
    lat: 36 + (Math.random() - 0.5) * 4,
    lon: -98 + (Math.random() - 0.5) * 8,
    intensity: 0.55 + Math.random() * 0.4,
    latScale: 4 + Math.random() * 3,
    lonScale: 5 + Math.random() * 4,
    shearBoost: 0.25,
    gulfMoisture: 0.12
  });

  // Adjust seeds by time to loosely mimic day-to-day patterns
  const timeShift = timeIndex * 4;
  return seeds.map(seed => ({
    ...seed,
    lat: seed.lat + (Math.random() - 0.5) * timeShift * 0.35,
    lon: seed.lon + (Math.random() - 0.5) * timeShift * 0.6
  }));
}

function gaussianContribution(value, scale) {
  return Math.exp(-Math.pow(value / scale, 2));
}

function generateProbabilityFeatures(timeWindow, timeIndex) {
  const latStart = 24;
  const latEnd = 50;
  const lonStart = -125;
  const lonEnd = -66;
  const latStep = 2;
  const lonStep = 2;

  const seeds = createStormSeeds(timeIndex);
  const features = [];

  for (let lat = latStart; lat < latEnd; lat += latStep) {
    for (let lon = lonStart; lon < lonEnd; lon += lonStep) {
      const centroid = {
        lat: lat + latStep / 2,
        lon: lon + lonStep / 2
      };

      let probability = 0;
      let keyDrivers = [];

      seeds.forEach(seed => {
        const dLat = centroid.lat - seed.lat;
        const dLon = centroid.lon - seed.lon;
        const distance = Math.sqrt(
          gaussianContribution(dLat, seed.latScale) + gaussianContribution(dLon, seed.lonScale)
        );

        const stormProbability = seed.intensity * Math.exp(-((Math.abs(dLat) / seed.latScale) ** 2 + (Math.abs(dLon) / seed.lonScale) ** 2));
        probability += stormProbability + seed.shearBoost * distance;

        if (stormProbability > 0.2) {
          keyDrivers.push({
            location: `${formatLatitude(seed.lat)}, ${formatLongitude(seed.lon)}`,
            influence: (stormProbability * 100).toFixed(1)
          });
        }
      });

      const gulfInfluence = Math.max(0, 1 - (centroid.lat - 26) / 16) * 0.25;
      const drylineInfluence = Math.max(0, 1 - Math.abs(centroid.lon + 100) / 12) * 0.18;
      probability += gulfInfluence + drylineInfluence;

      const cappedProbability = Math.min(75, probability * 100);
      const risk = getRiskLevel(cappedProbability);

      if (risk) {
        const feature = {
          type: "Feature",
          geometry: buildPolygon(lat, lon, latStep, lonStep),
          properties: {
            probability: Math.round(cappedProbability),
            riskLabel: risk.label,
            color: risk.color,
            label: timeWindow.label,
            centroid,
            influences: keyDrivers.slice(0, 3)
          }
        };
        features.push(feature);
      }
    }
  }

  return features;
}

function generateForecastSet() {
  const generatedAt = new Date();
  const forecast = TIME_WINDOWS.map((window, idx) => ({
    window,
    features: generateProbabilityFeatures(window, idx),
    generatedAt
  }));

  logStatus(`Forecast generated for ${generatedAt.toLocaleTimeString()}`);
  return forecast;
}

function updateInfoPanel({ probability, riskLabel, label, centroid, influences }) {
  const infoPanel = document.getElementById("info-panel");
  const infoBody = infoPanel.querySelector(".info-body");

  const riskText = riskLabel === "No Selection" ? "No active selection" : `${riskLabel} Risk`;
  const probabilityText = probability ? `${probability}%` : "--";

  const nearby = influences
    .map(driver => `<li><strong>${driver.influence}%</strong> driver near ${driver.location}</li>`)
    .join("") || "<li>Ambient moisture and shear.</li>";

  infoBody.innerHTML = `
    <p class="headline">${label} Outlook</p>
    <p class="prob"><strong>${probabilityText}</strong> probability &mdash; <span>${riskText}</span></p>
    <p class="location">Approximate center: ${formatLatitude(centroid.lat)}, ${formatLongitude(centroid.lon)}</p>
    <p class="drivers-title">Primary drivers:</p>
    <ul class="drivers">${nearby}</ul>
  `;
}

function renderForecast(timeIndex) {
  const forecastSlot = activeForecast[timeIndex];
  if (!forecastSlot) return;

  probabilityLayer.clearLayers();
  probabilityLayer.addData(forecastSlot.features);
  timeText.textContent = forecastSlot.window.label;
}

function logStatus(message) {
  const li = document.createElement("li");
  const timestamp = new Date().toLocaleTimeString();
  li.innerHTML = `<strong>${timestamp}</strong> &mdash; ${message}`;
  statusFeed.prepend(li);
  while (statusFeed.childElementCount > 6) {
    statusFeed.removeChild(statusFeed.lastChild);
  }
}

function initializeForecast() {
  activeForecast = generateForecastSet();
  renderForecast(parseInt(timeRange.value, 10));
}

function scheduleAutoRefresh() {
  if (autoRefreshHandle) {
    clearInterval(autoRefreshHandle);
  }
  autoRefreshHandle = setInterval(() => {
    logStatus("Auto-refreshing forecast outlook");
    initializeForecast();
  }, 90000);
}

timeRange.addEventListener("input", event => {
  const index = parseInt(event.target.value, 10);
  renderForecast(index);
});

generateBtn.addEventListener("click", () => {
  logStatus("Manual forecast regeneration requested");
  initializeForecast();
});

initializeForecast();
scheduleAutoRefresh();

// Initial info message
updateInfoPanel({
  probability: 0,
  riskLabel: "No Selection",
  label: TIME_WINDOWS[0].label,
  centroid: { lat: 37.5, lon: -97 },
  influences: []
});
