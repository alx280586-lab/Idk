const GRID_SIZE = 512;
const RADAR_ORIGIN = { x: GRID_SIZE * 0.45, y: GRID_SIZE * 0.55 };
const NYQUIST = 63;

export function createRadarState() {
  const size = GRID_SIZE * GRID_SIZE;
  return {
    size,
    reflectivity: new Float32Array(size),
    velocity: new Float32Array(size),
    spectrumWidth: new Float32Array(size),
    cc: new Float32Array(size),
    zdr: new Float32Array(size),
    kdp: new Float32Array(size),
    noise: new Float32Array(size)
  };
}

export function generateFields(radarState, atmoState, options) {
  const { storms } = atmoState;
  const { reflectivity, velocity, spectrumWidth, cc, zdr, kdp, noise } = radarState;
  const size = radarState.size;
  noise.fill(0);
  for (let i = 0; i < size; i++) {
    reflectivity[i] = 0;
    velocity[i] = 0;
    spectrumWidth[i] = 0.5;
    cc[i] = 0.98;
    zdr[i] = 0.5;
    kdp[i] = 0.1;
  }

  for (const storm of storms) {
    stampStorm(storm, radarState, options);
  }
  applyBackgroundNoise(radarState, atmoState, options);
  return radarState;
}

function stampStorm(storm, radarState, options) {
  const { reflectivity, velocity, spectrumWidth, cc, zdr, kdp } = radarState;
  const baseRadius = 30 + storm.intensity * 0.8;
  const rotationSign = storm.rotation > 0 ? 1 : -1;
  const hookBias = Math.min(1, storm.rotation * 0.8);

  for (let y = -baseRadius; y <= baseRadius; y++) {
    const gy = Math.floor(storm.y + y);
    if (gy < 0 || gy >= GRID_SIZE) continue;
    for (let x = -baseRadius; x <= baseRadius; x++) {
      const gx = Math.floor(storm.x + x);
      if (gx < 0 || gx >= GRID_SIZE) continue;
      const idx = gy * GRID_SIZE + gx;
      const dist = Math.hypot(x, y);
      if (dist > baseRadius) continue;
      const core = Math.exp(-(dist * dist) / (0.12 * baseRadius * baseRadius));
      let dBZ = storm.intensity * core;
      const hook = hookBias * Math.exp(-Math.pow((Math.atan2(y, x) + Math.PI / 2) / 1.4, 2));
      dBZ += hook * storm.intensity * 0.7;
      if (storm.phase === "rotation" && dist < baseRadius * 0.35) {
        dBZ *= 1.2;
      }
      if (storm.phase === "decay") {
        dBZ *= 0.7;
      }
      const attenuation = Math.exp(-dist / (baseRadius * 1.5));
      dBZ *= attenuation;
      if (storm.hydrometeors?.hail) {
        dBZ += storm.hydrometeors.hail * 20 * Math.exp(-(dist * dist) / (baseRadius * baseRadius * 0.4));
      }
      reflectivity[idx] = Math.max(reflectivity[idx], dBZ);

      const toRadar = {
        x: gx - RADAR_ORIGIN.x,
        y: gy - RADAR_ORIGIN.y
      };
      const range = Math.hypot(toRadar.x, toRadar.y) + 1e-5;
      const inbound =
        -((storm.rotation * rotationSign * -toRadar.y) / range) * 35 +
        (storm.rotation * toRadar.x) / range * 25 +
        (storm.type === "tropical" ? -storm.rotation * toRadar.y : 0);
      const translational = ((storm.x - RADAR_ORIGIN.x) * 0.05 + (storm.y - RADAR_ORIGIN.y) * -0.05);
      let vel = inbound + translational;
      if (!options.dealias && vel > NYQUIST) vel -= 2 * NYQUIST;
      if (!options.dealias && vel < -NYQUIST) vel += 2 * NYQUIST;
      velocity[idx] = clamp(vel, -NYQUIST, NYQUIST);

      const turbulence = 5 + storm.rotation * 30 * Math.exp(-(dist * dist) / (baseRadius * baseRadius * 0.3));
      spectrumWidth[idx] = Math.max(spectrumWidth[idx], turbulence);

      let corr = 0.98 - 0.2 * hookBias * Math.exp(-(dist * dist) / (baseRadius * baseRadius * 0.5));
      if (storm.debrisStrength > 0.4 && dist < baseRadius * 0.2) {
        corr -= storm.debrisStrength * 0.4;
      }
      cc[idx] = Math.min(cc[idx], corr);

      let zdrVal = 0.5 + hookBias * 2.5 * Math.max(0, Math.cos(Math.atan2(y, x) - Math.PI / 2));
      zdrVal -= (storm.hydrometeors?.hail || 0) * 1.5;
      zdr[idx] = Math.max(-1, Math.min(4, zdrVal));

      const rainRate = Math.max(0, dBZ - 20) * 0.03;
      kdp[idx] = Math.max(kdp[idx], rainRate * 0.4);
    }
  }
}

function applyBackgroundNoise(radarState, atmoState, options) {
  const { reflectivity, cc } = radarState;
  const { environment } = atmoState;
  for (let y = 0; y < GRID_SIZE; y++) {
    for (let x = 0; x < GRID_SIZE; x++) {
      const idx = y * GRID_SIZE + x;
      const range = Math.hypot(x - RADAR_ORIGIN.x, y - RADAR_ORIGIN.y);
      const attenuation = Math.exp(-range / 380);
      reflectivity[idx] *= attenuation + 0.2;
      if (range < 25 && !options.clutterFilter) {
        reflectivity[idx] = Math.max(reflectivity[idx], 18 + 5 * Math.sin(x * 0.5) * Math.cos(y * 0.5));
      }
      cc[idx] = Math.min(0.99, Math.max(0.55, cc[idx]));
    }
  }
}

export function blendFields(current, next, t) {
  const keys = ["reflectivity", "velocity", "spectrumWidth", "cc", "zdr", "kdp"];
  for (const key of keys) {
    const a = current[key];
    const b = next[key];
    for (let i = 0; i < a.length; i++) {
      a[i] = a[i] * (1 - t) + b[i] * t;
    }
  }
}

export const Radar = {
  create: createRadarState,
  generate: generateFields,
  blend: blendFields,
  GRID_SIZE,
  RADAR_ORIGIN,
  NYQUIST
};

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v));
}
