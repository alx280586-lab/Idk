const overviewFragments = {
  jets: [
    "a 110 kt subtropical jet punching into the southern Plains",
    "a cyclonically curved 95 kt midlevel jet streak nosing across the Ozarks",
    "a compact 120 kt polar jet core diving into the Four Corners",
    "a broad 80 kt upper-level jet arcing from the Baja Peninsula into the Mid-Mississippi Valley"
  ],
  surface: [
    "a sharpening dryline draped from western Oklahoma into central Texas",
    "a warm front surging northward through the Ohio Valley",
    "lee cyclogenesis underway across eastern Colorado",
    "a stalled boundary from the Carolinas into the Delmarva Peninsula"
  ],
  mesoscale: [
    "rich 70+°F dewpoints pooling ahead of the boundary",
    "a focused corridor of 300-400 m²/s² 0-1 km SRH",
    "steep midlevel lapse rates overspreading the warm sector",
    "a plume of elevated mixed-layer air advecting in from the Mexican Plateau"
  ],
  trigger: [
    "forcing for ascent increasing as height falls overspread the region",
    "low-level convergence maximizing near sunset as the low deepens",
    "a subtle shortwave trough emerging from New Mexico enhancing lift",
    "persistent warm advection sustaining elevated convection into the overnight"
  ]
};

const hazardCategories = ["MRGL", "SLGT", "ENH", "MDT", "HIGH"];
const riskPercentages = [5, 15, 30, 45, 60];
const tornadoPercentages = [2, 5, 10, 15, 30];

const stormModes = [
  "discrete supercells",
  "semi-discrete cells evolving into a QLCS",
  "a fast-moving bow echo",
  "a long-lived MCS with embedded mesovortices",
  "broken lines of supercells and splitting storms"
];

const narrativeElements = {
  evolution: [
    "Initial convection struggled to deepen until a focused zone of convergence overcame the lingering inhibition.",
    "Towering cumulus erupted in waves, each successive attempt tapping into deeper moisture and instability.",
    "As sunset approached, the boundary layer remained uncapped, and storms quickly intensified upon initiation.",
    "Cold pools surged southward but repeatedly modified the air mass, allowing new updrafts to remain surface based.",
    "Storm mergers proved decisive, transforming isolated cells into larger complexes that could sustain intense updrafts."
  ],
  tornadoes: [
    "One tornadic supercell cycled repeatedly, producing a family of tornadoes with varying intensity.",
    "A dramatic stovepipe tornado remained on the ground for nearly 40 minutes, carving a distinct damage path.",
    "Storm chasers documented a rain-wrapped tornado illuminated by power flashes and frequent lightning.",
    "Radar imagery captured a tight velocity couplet, with dual-polarization data highlighting lofted debris.",
    "Emergency managers relayed multiple reports of structural damage as tornadoes traversed rural communities."
  ],
  radar: [
    "Dual-pol radar detected large hail cores exceeding 70 dBZ, confirming the severity of the storms.",
    "Satellite imagery displayed overshooting tops and gravity waves radiating downwind from the strongest cells.",
    "A pronounced inflow notch and debris signature left little doubt about the ongoing tornadic activity.",
    "Regional radar mosaics showed storms congealing into a bowing segment racing toward the Mississippi River.",
    "Frequent lightning bursts flickered in rapid succession, signaling robust electrification within the storms."
  ],
  impacts: [
    "Local emergency management agencies activated search-and-rescue teams almost immediately.",
    "Power outages climbed into the tens of thousands as transmission lines suffered repeated strikes.",
    "Residents sought shelter in community safe rooms and storm shelters, crediting early warnings for their preparedness.",
    "Transportation corridors were briefly closed as debris and overturned vehicles blocked lanes.",
    "Public reports highlighted both the devastation and the remarkable survival stories emerging overnight."
  ],
  surprises: [
    "Forecasters noted a subtle low-level jet surge that amplified helicity beyond earlier projections.",
    "A pocket of enhanced instability materialized where morning clouds had been expected to linger.",
    "Anvil shadowing cooled the boundary layer just enough to delay additional development for an hour.",
    "Storm-scale interactions yielded an unexpected right-moving supercell that deviated toward richer moisture.",
    "Upscale growth occurred more quickly than forecast, forcing rapid adjustments to downstream warnings."
  ]
};

function randomInRange(min, max, decimals = 0) {
  const value = Math.random() * (max - min) + min;
  return Number(value.toFixed(decimals));
}

function pickRandom(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function weightedChoice(choices) {
  const totalWeight = choices.reduce((sum, choice) => sum + choice.weight, 0);
  const threshold = Math.random() * totalWeight;
  let cumulative = 0;
  for (const choice of choices) {
    cumulative += choice.weight;
    if (threshold <= cumulative) {
      return choice.value;
    }
  }
  return choices[choices.length - 1].value;
}

function generateOverview() {
  const paragraphs = [];
  for (let i = 0; i < 3; i++) {
    const jet = pickRandom(overviewFragments.jets);
    const surface = pickRandom(overviewFragments.surface);
    const mesoscale = pickRandom(overviewFragments.mesoscale);
    const trigger = pickRandom(overviewFragments.trigger);
    const mode = pickRandom(stormModes);
    const text = `A day-one outlook highlights ${jet}, with ${surface}. The warm sector features ${mesoscale}, supporting ${mode}. Meanwhile, ${trigger}.`;
    paragraphs.push(text);
  }
  return paragraphs;
}

function generateMetrics() {
  return {
    cape: randomInRange(800, 4000, 0),
    cin: randomInRange(-250, -25, 0),
    dewpoint: randomInRange(58, 76, 1),
    lapseRate: randomInRange(6, 8.5, 1),
    srh: randomInRange(150, 450, 0),
    ehi: randomInRange(1, 6, 1),
    bulkShear: randomInRange(25, 65, 0),
    stormMotion: randomInRange(35, 70, 0)
  };
}

function generateSoundingData(metrics) {
  const levels = [];
  const baseTemp = randomInRange(23, 30, 1); // surface Celsius
  const dewpointSpread = randomInRange(6, 12, 1);
  let temp = baseTemp;
  let dew = baseTemp - dewpointSpread;
  for (let p = 1000; p >= 100; p -= 25) {
    const heightFactor = (1000 - p) / 100;
    const lapseRate = metrics.lapseRate + randomInRange(-0.8, 0.8, 2);
    temp = baseTemp - (heightFactor * lapseRate);
    if (p > 800 && Math.random() < 0.2) {
      temp += randomInRange(2, 4, 1); // capping inversion
    }
    dew -= randomInRange(0.5, 1.5, 1);
    const windSpeed = randomInRange(10 + heightFactor * 3, 70, 0);
    const windDir = randomInRange(130 - heightFactor * 10, 270, 0);
    levels.push({
      pressure: p,
      temperature: temp,
      dewpoint: Math.max(temp - 25, dew),
      windSpeed,
      windDir
    });
  }
  return levels;
}

function drawSkewT(canvas, levels) {
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);

  ctx.fillStyle = "rgba(255,255,255,0.05)";
  ctx.fillRect(0, 0, width, height);

  // Grid lines
  ctx.strokeStyle = "rgba(255,255,255,0.08)";
  ctx.lineWidth = 1;
  for (let temp = -40; temp <= 40; temp += 10) {
    ctx.beginPath();
    const start = tempToX(temp, 1000, width);
    ctx.moveTo(start, 0);
    ctx.lineTo(start + height * skewFactor(), height);
    ctx.stroke();
  }

  const pressures = [1000, 900, 800, 700, 600, 500, 400, 300, 200, 100];
  ctx.font = "12px 'Segoe UI', sans-serif";
  ctx.fillStyle = "rgba(255,255,255,0.6)";
  pressures.forEach(p => {
    const y = pressureToY(p, height);
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.strokeStyle = "rgba(255,255,255,0.1)";
    ctx.stroke();
    ctx.fillText(`${p} mb`, 6, y - 4);
  });

  // Temperature line
  ctx.strokeStyle = "#ff884d";
  ctx.lineWidth = 2;
  ctx.beginPath();
  levels.forEach((level, index) => {
    const x = tempToX(level.temperature, level.pressure, width);
    const y = pressureToY(level.pressure, height);
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.stroke();

  // Dewpoint line
  ctx.strokeStyle = "#4dbbff";
  ctx.lineWidth = 2;
  ctx.beginPath();
  levels.forEach((level, index) => {
    const x = tempToX(level.dewpoint, level.pressure, width);
    const y = pressureToY(level.pressure, height);
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.stroke();

  // Parcel trace approximation
  ctx.strokeStyle = "#fff562";
  ctx.setLineDash([6, 4]);
  ctx.beginPath();
  let parcelTemp = levels[0].temperature;
  levels.forEach((level, index) => {
    const x = tempToX(parcelTemp, level.pressure, width);
    const y = pressureToY(level.pressure, height);
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
    parcelTemp -= 9.8 * ((levels[index - 1]?.pressure ?? level.pressure) - level.pressure) / 100;
  });
  ctx.stroke();
  ctx.setLineDash([]);
}

function skewFactor() {
  return 0.4;
}

function tempToX(tempC, pressure, width) {
  const scale = 6; // pixels per °C
  const skew = skewFactor();
  return width / 2 + (tempC + skew * Math.log(pressure / 1000) * 40) * scale;
}

function pressureToY(pressure, height) {
  const logMin = Math.log(100);
  const logMax = Math.log(1050);
  const y = (Math.log(pressure) - logMax) / (logMin - logMax);
  return y * height;
}

function drawHodograph(canvas, levels) {
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "rgba(255,255,255,0.05)";
  ctx.fillRect(0, 0, width, height);

  const centerX = width / 2;
  const centerY = height / 2;
  const maxRadius = Math.min(width, height) / 2 - 10;

  ctx.strokeStyle = "rgba(255,255,255,0.1)";
  ctx.lineWidth = 1;
  for (let speed = 10; speed <= 70; speed += 10) {
    const radius = (speed / 70) * maxRadius;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillStyle = "rgba(255,255,255,0.35)";
    ctx.fillText(`${speed} kt`, centerX + radius + 4, centerY - 4);
  }

  ctx.strokeStyle = "#ff6fd8";
  ctx.lineWidth = 2;
  ctx.beginPath();
  levels.forEach((level, index) => {
    const radians = (level.windDir - 90) * (Math.PI / 180);
    const radius = (level.windSpeed / 70) * maxRadius;
    const x = centerX + Math.cos(radians) * radius;
    const y = centerY + Math.sin(radians) * radius;
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.stroke();
}

function renderOverview(paragraphs, metrics) {
  const overviewText = document.getElementById("overviewText");
  overviewText.innerHTML = paragraphs.map(p => `<p>${p}</p>`).join("");

  const metricsGrid = document.getElementById("environmentMetrics");
  metricsGrid.innerHTML = "";
  const entries = [
    { label: "MLCAPE", value: `${metrics.cape} J/kg` },
    { label: "MLCIN", value: `${metrics.cin} J/kg` },
    { label: "Surface Dewpoint", value: `${metrics.dewpoint} °F` },
    { label: "Midlevel Lapse Rate", value: `${metrics.lapseRate} °C/km` },
    { label: "0-1 km SRH", value: `${metrics.srh} m²/s²` },
    { label: "0-1 km EHI", value: `${metrics.ehi}` },
    { label: "0-6 km Shear", value: `${metrics.bulkShear} kt` },
    { label: "Storm Motion", value: `${metrics.stormMotion} kt` }
  ];
  entries.forEach(entry => {
    const div = document.createElement("div");
    div.className = "metric";
    div.innerHTML = `<span class="label">${entry.label}</span><span class="value">${entry.value}</span>`;
    metricsGrid.appendChild(div);
  });
}

function generateTruth(metrics) {
  const severityIndex = (metrics.cape / 2000) + (metrics.srh / 150) + (metrics.bulkShear / 40);
  const overall = hazardCategories[Math.min(hazardCategories.length - 1, Math.round(severityIndex / 2))];
  const wind = riskPercentages[Math.min(riskPercentages.length - 1, Math.round(metrics.bulkShear / 15))];
  const hail = riskPercentages[Math.min(riskPercentages.length - 1, Math.round(metrics.cape / 800))];
  const tor = tornadoPercentages[Math.min(tornadoPercentages.length - 1, Math.round(metrics.srh / 120))];
  return {
    overall,
    wind,
    hail,
    tornado: tor,
    hatched: {
      wind: metrics.bulkShear > 45,
      hail: metrics.cape > 2800,
      tornado: metrics.srh > 300 && metrics.ehi > 2.5
    }
  };
}

function simulateTimeline(metrics) {
  const entries = [];
  const baseTimes = ["16Z", "18Z", "20Z", "22Z", "00Z", "03Z", "06Z"];
  baseTimes.forEach(time => {
    const phrase = pickRandom(narrativeElements.evolution);
    const mode = pickRandom(stormModes);
    const srhMention = metrics.srh > 300 ? "SRH values remained extremely supportive of tornado potential." : "Wind profiles supported organized convection.";
    entries.push({ time, text: `${time} | ${phrase} Dominant storm mode: ${mode}. ${srhMention}` });
  });
  return entries;
}

function buildParagraph(sentences) {
  return sentences.join(" ");
}

function generateNarrativeParagraphs(metrics, truth) {
  const paragraphs = [];
  const paragraphCount = randomInRange(10, 15, 0);
  for (let i = 0; i < paragraphCount; i++) {
    const sentences = [];
    sentences.push(pickRandom(narrativeElements.evolution));
    sentences.push(pickRandom(narrativeElements.tornadoes));
    sentences.push(pickRandom(narrativeElements.radar));
    sentences.push(pickRandom(narrativeElements.impacts));
    sentences.push(pickRandom(narrativeElements.surprises));
    sentences.push(`Observed hail reports frequently exceeded ${truth.hail}% probability markers, underscoring the hail threat.`);
    sentences.push(`Wind damage corresponded with forecast ${truth.wind}% probabilities, though localized swaths exceeded expectations.`);
    paragraphs.push(buildParagraph(sentences));
  }
  return paragraphs;
}

function createDamageEvents(truth) {
  const eventTypes = ["Tornado", "Significant Hail", "Destructive Wind"];
  const events = [];
  const locations = ["Norman, OK", "Springfield, MO", "Tupelo, MS", "Evansville, IN", "Lubbock, TX", "Jackson, MS", "Shreveport, LA"];
  const efRatings = ["EF1", "EF2", "EF3", "EF4"];
  for (let i = 0; i < 3; i++) {
    const type = eventTypes[i % eventTypes.length];
    const fatalities = randomInRange(0, truth.tornado >= 15 ? 5 : 1, 0);
    const injuries = randomInRange(fatalities, fatalities + 25, 0);
    const damage = randomInRange(2, 200, 1) * 1_000_000;
    const rating = type === "Tornado" ? pickRandom(efRatings) : `${randomInRange(2, 4, 0)}" Hail`;
    const location = pickRandom(locations);
    events.push({ type, fatalities, injuries, damage, rating, location });
  }
  return events;
}

function formatUSD(amount) {
  return amount.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

function renderDamageTable(events) {
  const tbody = document.querySelector("#damageTable tbody");
  tbody.innerHTML = "";
  events.forEach(evt => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${evt.type}</td>
      <td>${evt.fatalities}</td>
      <td>${evt.injuries}</td>
      <td>${formatUSD(evt.damage)}</td>
      <td>${evt.rating}</td>
      <td>${evt.location}</td>
    `;
    tbody.appendChild(row);
  });
}

function generateDeepDive(event, metrics, truth) {
  const paragraphs = [];
  const count = randomInRange(10, 12, 0);
  for (let i = 0; i < count; i++) {
    const sentences = [];
    sentences.push(`The ${event.type.toLowerCase()} affecting ${event.location} initiated as boundary layer theta-e values peaked during the late afternoon.`);
    sentences.push(`Radar interrogation revealed persistent inflow notches, coinciding with ${metrics.bulkShear} kt of deep-layer shear.`);
    sentences.push(`Surface observations confirmed dewpoints in the mid ${Math.round(metrics.dewpoint)}s, maintaining buoyancy that fed successive updrafts.`);
    sentences.push(`Emergency management described coordinated responses that limited casualties to ${event.fatalities} fatalities and ${event.injuries} injuries.`);
    sentences.push(`The event's ${event.rating} rating aligned with surveyed damage indicators and high-resolution velocity estimates.`);
    sentences.push(`Storm chasers reported dramatic structure, noting ${pickRandom(stormModes)} evolving near the core.`);
    sentences.push(`In the aftermath, recovery crews documented damage totals approaching ${formatUSD(event.damage)}, prompting disaster declarations.`);
    paragraphs.push(buildParagraph(sentences));
  }
  return paragraphs;
}

function renderDeepDives(events, metrics, truth) {
  const container = document.getElementById("eventDeepDives");
  container.innerHTML = "";
  events.forEach((event, idx) => {
    const wrapper = document.createElement("div");
    wrapper.className = "deep-dive";
    const paragraphs = generateDeepDive(event, metrics, truth);
    wrapper.innerHTML = `<h3>${event.type} – ${event.location}</h3>` + paragraphs.map(p => `<p>${p}</p>`).join("");
    container.appendChild(wrapper);
  });
}

function computeScores(forecast, truth) {
  const catScore = 100 - Math.abs(hazardCategories.indexOf(forecast.overallCategory) - hazardCategories.indexOf(truth.overall)) * 15;
  const windScore = 100 - Math.abs(Number(forecast.windRisk) - truth.wind) * 2;
  const hailScore = 100 - Math.abs(Number(forecast.hailRisk) - truth.hail) * 2;
  const torScore = 100 - Math.abs(Number(forecast.tornadoRisk) - truth.tornado) * 3;
  const hatchedMapping = [
    { forecastKey: "windHatched", truthKey: "wind" },
    { forecastKey: "hailHatched", truthKey: "hail" },
    { forecastKey: "torHatched", truthKey: "tornado" }
  ];
  const hatchedBonus = hatchedMapping.reduce((sum, mapping) => {
    const forecastFlag = forecast[mapping.forecastKey];
    const truthFlag = truth.hatched[mapping.truthKey];
    if (forecastFlag === truthFlag) return sum + 5;
    if (forecastFlag && !truthFlag) return sum - 5;
    return sum;
  }, 0);
  const accuracy = Math.max(0, Math.round((catScore + windScore + hailScore + torScore + hatchedBonus) / 4));
  const hitRate = Math.max(0, Math.min(100, Math.round(100 - Math.abs(Number(forecast.tornadoRisk) - truth.tornado) * 2)));
  const falseAlarm = Math.max(0, Math.min(100, Math.round(Math.abs(Number(forecast.windRisk) - truth.wind) * 1.5)));
  const csiNumerator = 100 - Math.abs(Number(forecast.hailRisk) - truth.hail);
  const csi = Math.max(0, Math.min(100, Math.round(csiNumerator - falseAlarm / 2)));
  const publicImpact = Math.max(0, Math.min(100, Math.round((accuracy + hitRate - falseAlarm / 2) / 2)));
  return {
    accuracy,
    hitRate,
    falseAlarm,
    csi,
    publicImpact
  };
}

function renderScores(scores) {
  const summary = document.getElementById("scoreSummary");
  summary.innerHTML = "";
  const labels = [
    { label: "Forecast Accuracy", value: `${scores.accuracy}%` },
    { label: "Hit Rate", value: `${scores.hitRate}%` },
    { label: "False Alarm Rate", value: `${scores.falseAlarm}%` },
    { label: "Critical Success Index", value: `${scores.csi}` },
    { label: "Public Safety Impact", value: `${scores.publicImpact}%` }
  ];
  labels.forEach(item => {
    const div = document.createElement("div");
    div.className = "score-card";
    div.innerHTML = `<strong>${item.label}</strong><p>${item.value}</p>`;
    summary.appendChild(div);
  });
}

let currentScenario = null;

function initializeScenario() {
  const overview = generateOverview();
  const metrics = generateMetrics();
  const sounding = generateSoundingData(metrics);
  const truth = generateTruth(metrics);
  currentScenario = {
    id: Date.now(),
    overview,
    metrics,
    sounding,
    truth,
    forecast: null,
    timeline: [],
    events: []
  };
  renderOverview(overview, metrics);
  drawSkewT(document.getElementById("soundingCanvas"), sounding);
  drawHodograph(document.getElementById("hodographCanvas"), sounding);
  document.getElementById("simulationSection").classList.add("hidden");
  document.getElementById("recapSection").classList.add("hidden");
  document.getElementById("scoreSection").classList.add("hidden");
}

function regenerateSounding() {
  if (!currentScenario) return;
  currentScenario.sounding = generateSoundingData(currentScenario.metrics);
  drawSkewT(document.getElementById("soundingCanvas"), currentScenario.sounding);
  drawHodograph(document.getElementById("hodographCanvas"), currentScenario.sounding);
}

function handleForecastSubmission(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const forecast = {
    overallCategory: formData.get("overallCategory"),
    windRisk: formData.get("windRisk"),
    hailRisk: formData.get("hailRisk"),
    tornadoRisk: formData.get("tornadoRisk"),
    windHatched: formData.get("windHatched") === "on",
    hailHatched: formData.get("hailHatched") === "on",
    torHatched: formData.get("torHatched") === "on",
    discussion: formData.get("discussion") || "No discussion provided."
  };
  currentScenario.forecast = forecast;
  currentScenario.timeline = simulateTimeline(currentScenario.metrics);
  renderTimeline(currentScenario.timeline, forecast);
  document.getElementById("simulationSection").classList.remove("hidden");
  document.getElementById("recapSection").classList.add("hidden");
  document.getElementById("scoreSection").classList.add("hidden");
}

function renderTimeline(timeline, forecast) {
  const container = document.getElementById("simulationTimeline");
  container.innerHTML = `
    <div class="timeline-entry">
      <strong>Discussion Recap</strong>
      <p>${forecast.discussion}</p>
    </div>
  `;
  timeline.forEach(entry => {
    const div = document.createElement("div");
    div.className = "timeline-entry";
    div.innerHTML = `<strong>${entry.time}</strong><p>${entry.text}</p>`;
    container.appendChild(div);
  });
}

function handleGenerateRecap() {
  if (!currentScenario || !currentScenario.forecast) return;
  currentScenario.events = createDamageEvents(currentScenario.truth);
  const paragraphs = generateNarrativeParagraphs(currentScenario.metrics, currentScenario.truth);
  const recapContainer = document.getElementById("recapNarrative");
  recapContainer.innerHTML = paragraphs.map(p => `<p>${p}</p>`).join("");
  renderDamageTable(currentScenario.events);
  renderDeepDives(currentScenario.events, currentScenario.metrics, currentScenario.truth);
  const scores = computeScores(currentScenario.forecast, currentScenario.truth);
  renderScores(scores);
  document.getElementById("recapSection").classList.remove("hidden");
  document.getElementById("scoreSection").classList.remove("hidden");
}

document.addEventListener("DOMContentLoaded", () => {
  initializeScenario();
  document.getElementById("newScenario").addEventListener("click", () => {
    initializeScenario();
    document.getElementById("outlookForm").reset();
  });
  document.getElementById("regenerateSounding").addEventListener("click", regenerateSounding);
  document.getElementById("outlookForm").addEventListener("submit", handleForecastSubmission);
  document.getElementById("generateRecap").addEventListener("click", handleGenerateRecap);
});
