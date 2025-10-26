const GRID_SIZE = 512;
const CELL_KM = 5;
const DAY_MINUTES = 1440;

export function createRandom(seed) {
  let state = seed >>> 0;
  return () => {
    state = Math.imul(state ^ (state >>> 15), 1 | state);
    state = state + Math.imul(state ^ (state >>> 7), 61 | state);
    return ((state ^ (state >>> 14)) >>> 0) / 4294967296;
  };
}

export function createAtmo(seed = 0x1337c0de) {
  const rand = createRandom(seed);
  const storms = [];
  const environment = {
    temperature: new Float32Array(GRID_SIZE * GRID_SIZE),
    dewpoint: new Float32Array(GRID_SIZE * GRID_SIZE),
    meanFlow: { u: 15, v: -5 },
    shear: { u: 25, v: 5 },
    dayFraction: 0,
    seed,
    rand
  };
  seedBackground(environment);
  spawnInitialStorms(storms, environment, rand);
  return { storms, environment, timeMinutes: 0 };
}

function seedBackground(env) {
  const { temperature, dewpoint, rand } = env;
  for (let y = 0; y < GRID_SIZE; y++) {
    for (let x = 0; x < GRID_SIZE; x++) {
      const idx = y * GRID_SIZE + x;
      const lat = 25 + (y / GRID_SIZE) * 25;
      const lon = -125 + (x / GRID_SIZE) * 55;
      const base = 15 + 10 * Math.sin((lat - 25) * Math.PI / 40);
      const diurnal = 5 * Math.cos((lon + 100) * Math.PI / 180);
      temperature[idx] = base + diurnal + 2 * (rand() - 0.5);
      dewpoint[idx] = temperature[idx] - (4 + 6 * (1 - Math.exp(-(lat - 25) / 10)));
    }
  }
}

function spawnInitialStorms(storms, env, rand) {
  const seeds = [
    { x: 0.35, y: 0.55, type: "plains" },
    { x: 0.55, y: 0.45, type: "midwest" },
    { x: 0.65, y: 0.7, type: "gulf" }
  ];
  seeds.forEach((seed, i) => {
    storms.push(createStorm(seed.x, seed.y, env, rand, i));
  });
}

function createStorm(nx, ny, env, rand, id) {
  const intensity = 40 + rand() * 30;
  const orientation = rand() * Math.PI * 2;
  const majorAxis = 28 + rand() * 22;
  const minorAxis = majorAxis * (0.55 + rand() * 0.2);
  return {
    id: id ?? Math.floor(rand() * 1e6),
    x: nx * GRID_SIZE,
    y: ny * GRID_SIZE,
    altitude: 7 + rand() * 5,
    intensity,
    rotation: 0.3 + rand() * 0.5,
    phase: "initiation",
    hydrometeors: {
      rain: 0.7,
      hail: 0.1,
      snow: 0,
      debris: 0
    },
    orientation,
    majorAxis,
    minorAxis,
    anvilRadius: majorAxis * (1.8 + rand() * 0.6),
    motion: { x: 0, y: 0 },
    tilt: 8 + rand() * 6,
    lifetime: 0,
    ageMinutes: 0,
    debrisStrength: 0,
    type: "supercell",
    updraft: 15 + rand() * 20,
    downdraft: 5 + rand() * 5,
    track: []
  };
}

export function updateAtmosphere(state, dtMinutes, options) {
  const { environment, storms } = state;
  environment.dayFraction = (state.timeMinutes + dtMinutes) / DAY_MINUTES;
  const diurnalPhase = Math.sin(environment.dayFraction * Math.PI * 2);
  environment.meanFlow.u = 10 + 15 * diurnalPhase;
  environment.meanFlow.v = -3 + 4 * Math.sin(environment.dayFraction * Math.PI * 4);
  environment.shear.u = 20 + 10 * environment.dayFraction;
  environment.shear.v = 8 + 8 * (1 - environment.dayFraction);
  advectThermodynamics(environment, dtMinutes, options);

  for (const storm of storms) {
    updateStorm(storm, environment, dtMinutes, options);
  }

  const spawnChance = Math.max(0.01, Math.abs(dtMinutes) * 0.01);
  if (environment.rand() < spawnChance) {
    storms.push(seedNewStorm(environment, options));
  }

  for (let i = storms.length - 1; i >= 0; i--) {
    if (storms[i].phase === "dissipated") {
      storms.splice(i, 1);
    }
  }

  state.timeMinutes = (state.timeMinutes + dtMinutes + DAY_MINUTES) % DAY_MINUTES;
}

function advectThermodynamics(env, dtMinutes, options) {
  const { temperature, dewpoint } = env;
  const advectFactor = (dtMinutes / 60) * 0.02;
  const diurnalBoost = options.diurnal ? Math.sin(env.dayFraction * Math.PI * 2) : 0;
  for (let i = 0; i < temperature.length; i++) {
    const moisture = options.moisture ? 2 : 0;
    temperature[i] += advectFactor * diurnalBoost;
    dewpoint[i] += advectFactor * (diurnalBoost + moisture * 0.1);
    dewpoint[i] = Math.min(dewpoint[i], temperature[i] - 1);
  }
}

function updateStorm(storm, env, dtMinutes, options) {
  const { meanFlow, shear, rand } = env;
  const moveFactor = dtMinutes / 10;
  const prevX = storm.x;
  const prevY = storm.y;
  storm.x += (meanFlow.u + 5 * (rand() - 0.5)) * moveFactor;
  storm.y += (meanFlow.v + 5 * (rand() - 0.5)) * moveFactor;
  storm.x = (storm.x + GRID_SIZE) % GRID_SIZE;
  storm.y = (storm.y + GRID_SIZE) % GRID_SIZE;
  if (Math.abs(dtMinutes) > 0.001) {
    let dx = storm.x - prevX;
    let dy = storm.y - prevY;
    if (dx > GRID_SIZE / 2) dx -= GRID_SIZE;
    if (dx < -GRID_SIZE / 2) dx += GRID_SIZE;
    if (dy > GRID_SIZE / 2) dy -= GRID_SIZE;
    if (dy < -GRID_SIZE / 2) dy += GRID_SIZE;
    storm.motion.x = dx / dtMinutes;
    storm.motion.y = dy / dtMinutes;
  }

  storm.ageMinutes += dtMinutes;
  storm.lifetime += dtMinutes;
  if (storm.ageMinutes < 60) {
    storm.phase = "initiation";
  } else if (storm.ageMinutes < 120) {
    storm.phase = "mature";
  } else if (storm.ageMinutes < 180) {
    storm.phase = "rotation";
  } else {
    storm.phase = "decay";
  }
  if (storm.ageMinutes > 210) {
    storm.phase = "dissipated";
  }

  const shearMag = Math.hypot(shear.u, shear.v);
  storm.rotation = 0.2 + 0.8 * Math.min(1, shearMag / 40);
  if (storm.phase === "rotation") {
    storm.debrisStrength = Math.min(1, storm.debrisStrength + dtMinutes * 0.01 * options.tornadoFactor);
  } else {
    storm.debrisStrength = Math.max(0, storm.debrisStrength - dtMinutes * 0.02);
  }

  storm.intensity += (rand() - 0.5) * dtMinutes * 0.4;
  storm.intensity = Math.max(20, Math.min(80, storm.intensity));

  const targetOrientation = Math.atan2(meanFlow.v + shear.v * 0.3, meanFlow.u + shear.u * 0.3);
  const trackAngle = Math.atan2(storm.motion.y || 0.0001, storm.motion.x || 0.0001);
  storm.orientation = blendAngles(storm.orientation, lerpAngle(trackAngle, targetOrientation, 0.5), 0.08);
  const targetMajor = 24 + storm.intensity * 0.55;
  const targetMinor = targetMajor * (0.5 + Math.min(0.4, shearMag / 60));
  storm.majorAxis += (targetMajor - storm.majorAxis) * 0.05;
  storm.minorAxis += (targetMinor - storm.minorAxis) * 0.05;
  storm.anvilRadius += (storm.majorAxis * 2.1 - storm.anvilRadius) * 0.03;

  storm.track.push({ x: storm.x, y: storm.y, age: 0, tornadic: storm.debrisStrength > 0.6 });
  if (storm.track.length > 120) storm.track.shift();
  for (const step of storm.track) {
    step.age += dtMinutes;
  }
}

function seedNewStorm(env, options) {
  const { rand } = env;
  const corridor = rand();
  let nx = 0.4 + 0.2 * rand();
  let ny = 0.5 + 0.2 * rand();
  let type = "supercell";
  if (corridor < 0.3) {
    nx = 0.3 + 0.3 * rand();
    ny = 0.35 + 0.2 * rand();
    type = "squall";
  } else if (corridor > 0.7) {
    nx = 0.55 + 0.25 * rand();
    ny = 0.6 + 0.25 * rand();
    type = "tropical";
  }
  const storm = createStorm(nx, ny, env, rand);
  storm.type = type;
  if (type === "tropical") {
    storm.rotation = 0.2;
    storm.intensity = 35 + rand() * 15;
  }
  if (type === "squall") {
    storm.rotation = 0.15 + rand() * 0.3;
    storm.intensity = 45 + rand() * 20;
  }
  if (!options.diurnal) {
    storm.phase = "mature";
    storm.ageMinutes = 90;
  }
  return storm;
}

export const Atmosphere = {
  create: createAtmo,
  update: updateAtmosphere
};

function blendAngles(current, target, factor) {
  const diff = normalizeAngle(target - current);
  return current + diff * factor;
}

function lerpAngle(a, b, t) {
  const diff = normalizeAngle(b - a);
  return a + diff * t;
}

function normalizeAngle(angle) {
  while (angle > Math.PI) angle -= Math.PI * 2;
  while (angle < -Math.PI) angle += Math.PI * 2;
  return angle;
}
