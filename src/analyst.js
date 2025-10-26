export function createAnalyst() {
  return {
    elapsed: 0,
    cadence: 10,
    log: []
  };
}

export function updateAnalyst(analyst, storms, timeMinutes, logEl) {
  analyst.elapsed += 1;
  if (analyst.elapsed < analyst.cadence) return;
  analyst.elapsed = 0;
  const lines = storms.slice(0, 3).map((storm) => describeStorm(storm));
  const summary = lines.join(" \u2022 ");
  if (!summary) return;
  const timestamp = formatTime(timeMinutes);
  const paragraph = document.createElement("p");
  paragraph.textContent = `${timestamp}Z – ${summary}`;
  logEl.prepend(paragraph);
  analyst.log.push({ time: timestamp, summary });
  while (logEl.children.length > 20) {
    logEl.removeChild(logEl.lastChild);
  }
}

function describeStorm(storm) {
  const phases = {
    initiation: "new convection organizing",
    mature: "mature core",
    rotation: storm.debrisStrength > 0.5 ? "intense tornadic rotation" : "mesocyclone",
    decay: "weakening and spreading out"
  };
  const typeLabel = storm.type === "tropical" ? "tropical band" : storm.type === "squall" ? "QLCS" : "supercell";
  const rot = Math.round(storm.rotation * 90);
  const refl = Math.round(storm.intensity);
  return `${typeLabel.toUpperCase()} ${storm.id} ${phases[storm.phase]} – ${refl} dBZ core, ${rot} kt rotation`;
}

function formatTime(minutes) {
  const mins = Math.floor(minutes % 60)
    .toString()
    .padStart(2, "0");
  const hour = Math.floor(minutes / 60)
    .toString()
    .padStart(2, "0");
  return `${hour}${mins}`;
}

export const Analyst = {
  create: createAnalyst,
  update: updateAnalyst
};
