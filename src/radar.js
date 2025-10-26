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
  const { storms, environment } = atmoState;
  const { reflectivity, velocity, spectrumWidth, cc, zdr, kdp, noise } = radarState;
  seedBackground(radarState, environment, options);

  for (const storm of storms) {
    stampStorm(storm, radarState, environment, options);
  }

  applyBackgroundArtifacts(radarState, environment, options);
  finalizeFields(radarState);
  return radarState;
}

function stampStorm(storm, radarState, environment, options) {
  const { reflectivity, velocity, spectrumWidth, cc, zdr, kdp } = radarState;
  const cos = Math.cos(storm.orientation);
  const sin = Math.sin(storm.orientation);
  const major = Math.max(18, storm.majorAxis);
  const minor = Math.max(12, storm.minorAxis);
  const anvil = Math.max(major * 1.5, storm.anvilRadius);
  const radius = Math.ceil(anvil);
  const hailFactor = storm.hydrometeors?.hail ?? 0;
  const debris = storm.debrisStrength || 0;
  const motion = storm.motion || { x: 0, y: 0 };

  for (let dy = -radius; dy <= radius; dy++) {
    const gy = Math.floor(storm.y + dy);
    if (gy < 0 || gy >= GRID_SIZE) continue;
    for (let dx = -radius; dx <= radius; dx++) {
      const gx = Math.floor(storm.x + dx);
      if (gx < 0 || gx >= GRID_SIZE) continue;
      const idx = gy * GRID_SIZE + gx;

      const relX = gx - storm.x;
      const relY = gy - storm.y;
      const alignedX = relX * cos + relY * sin;
      const alignedY = -relX * sin + relY * cos;
      const ell = Math.sqrt((alignedX * alignedX) / (major * major) + (alignedY * alignedY) / (minor * minor));
      if (ell > 2.2) continue;

      const rangeVecX = gx - RADAR_ORIGIN.x;
      const rangeVecY = gy - RADAR_ORIGIN.y;
      const range = Math.hypot(rangeVecX, rangeVecY) + 1e-6;
      const beamX = rangeVecX / range;
      const beamY = rangeVecY / range;
      const stormDist = Math.hypot(relX, relY) + 1e-6;

      const shield = Math.exp(-Math.max(0, ell - 1.1) * Math.max(0, ell - 1.1) * 1.8);
      let dBZ = 18 + storm.intensity * 0.25 * shield;
      const core = Math.exp(-(ell * ell) * 1.6);
      dBZ = Math.max(dBZ, 35 + storm.intensity * 0.55 * core);
      const hailCore = Math.exp(-Math.pow(stormDist / (Math.min(major, minor) * 0.55), 2.6));
      dBZ = Math.max(dBZ, 45 + storm.intensity * 0.35 * core + hailFactor * 30 * hailCore);

      const hookAngle = Math.atan2(alignedY + minor * 0.15, alignedX + major * 0.2);
      const hookRadius = Math.sqrt(
        ((alignedX + major * 0.25) ** 2) / (major * major * 0.6) +
          ((alignedY + minor * 0.05) ** 2) / (minor * minor * 0.45)
      );
      const hook = Math.exp(-Math.pow(hookRadius, 2.2)) * Math.exp(-hookAngle * hookAngle * 0.6);
      if (alignedX < major * 0.2 && alignedY < minor * 0.65) {
        dBZ = Math.max(dBZ, 40 + hook * storm.intensity * 0.7);
      }

      const inflowNotch = Math.exp(
        -((alignedX + major * 0.35) ** 2) / (major * major * 0.6) - (alignedY / (minor * 0.8)) ** 2
      );
      if (alignedX < -major * 0.1 && alignedY > -minor * 0.4) {
        dBZ *= 1 - inflowNotch * 0.55;
      }

      if (storm.phase === "decay") {
        dBZ *= 0.65;
      } else if (storm.phase === "rotation" && stormDist < Math.min(major, minor) * 0.6) {
        dBZ += 6 * storm.rotation;
      }

      const rangeAtten = Math.exp(-range / 520);
      dBZ = dBZ * rangeAtten + (spatialNoise(gx, gy, environment.seed) - 0.5) * 1.6;
      dBZ = Math.max(0, dBZ);

      reflectivity[idx] = Math.max(reflectivity[idx], dBZ);

      const tangentialSpeed = storm.rotation * 55 * Math.exp(-Math.pow(stormDist / Math.max(major, minor), 1.3));
      const tangentX = -relY / stormDist;
      const tangentY = relX / stormDist;
      const rotationVx = tangentX * tangentialSpeed;
      const rotationVy = tangentY * tangentialSpeed;
      const translationScale = 34;
      const translationVx = motion.x * translationScale + environment.meanFlow.u * 0.4;
      const translationVy = motion.y * translationScale + environment.meanFlow.v * 0.4;
      const rearInflow =
        -25 * Math.exp(-((alignedX + major * 0.05) ** 2) / (major * major * 0.5)) *
        Math.exp(-(alignedY / (minor * 0.7)) ** 2);
      const inflowVectorX = cos * rearInflow;
      const inflowVectorY = sin * rearInflow;
      let radialVelocity =
        rotationVx * beamX +
        rotationVy * beamY +
        translationVx * beamX +
        translationVy * beamY +
        inflowVectorX * beamX +
        inflowVectorY * beamY;

      if (!options.dealias) {
        while (radialVelocity > NYQUIST) radialVelocity -= 2 * NYQUIST;
        while (radialVelocity < -NYQUIST) radialVelocity += 2 * NYQUIST;
      }
      velocity[idx] = clamp(radialVelocity, -NYQUIST, NYQUIST);

      const shearTurb = Math.max(1.2, tangentialSpeed * 0.18) + Math.abs(rearInflow) * 0.05;
      spectrumWidth[idx] = Math.max(spectrumWidth[idx], shearTurb);

      let corr = 0.985 - shield * 0.08;
      if (hailFactor > 0.4) {
        corr -= hailCore * hailFactor * 0.2;
      }
      if (debris > 0.15 && stormDist < Math.min(major, minor) * 0.35) {
        corr -= debris * 0.5 * Math.exp(-Math.pow(stormDist / (minor * 0.5), 3));
      }
      cc[idx] = Math.min(cc[idx], Math.max(0.45, corr));

      let zdrVal = 0.3 + 2.6 * Math.exp(-Math.pow((alignedY - minor * 0.4) / (minor * 0.9), 2)) * Math.max(0, alignedX / major);
      zdrVal -= hailCore * 1.8 * hailFactor;
      zdr[idx] = clamp(zdrVal, -1.5, 4.5);

      const kdpVal = Math.max(0, (dBZ - 35) * 0.04) * (1 + hailFactor * 0.3);
      kdp[idx] = Math.max(kdp[idx], kdpVal);
    }
  }
}

function seedBackground(radarState, environment, options) {
  const { reflectivity, velocity, spectrumWidth, cc, zdr, kdp, noise } = radarState;
  const { meanFlow, seed, dayFraction } = environment;
  const sinPhase = Math.sin(dayFraction * Math.PI * 2);
  for (let y = 0; y < GRID_SIZE; y++) {
    for (let x = 0; x < GRID_SIZE; x++) {
      const idx = y * GRID_SIZE + x;
      const dx = x - RADAR_ORIGIN.x;
      const dy = y - RADAR_ORIGIN.y;
      const range = Math.hypot(dx, dy) + 1e-5;
      const az = Math.atan2(dy, dx);
      const baseNoise = spatialNoise(x, y, seed);
      const clearAir = 3 + 4 * Math.exp(-range / 240) + (baseNoise - 0.5) * 2.2;
      const sunBoost = sinPhase > 0 ? sinPhase * 1.5 * Math.max(0, Math.cos(az - Math.PI / 2)) : 0;
      reflectivity[idx] = Math.max(0, clearAir + sunBoost);

      const flowVx = meanFlow.u * 0.6;
      const flowVy = meanFlow.v * 0.6;
      const radial = (flowVx * dx + flowVy * dy) / range;
      velocity[idx] = clamp(radial, -NYQUIST, NYQUIST);

      spectrumWidth[idx] = 1.2 + (baseNoise - 0.5) * 0.4;
      cc[idx] = 0.99;
      zdr[idx] = 0.2 + (baseNoise - 0.5) * 0.1;
      kdp[idx] = 0.05;
      noise[idx] = baseNoise;
    }
  }

  if (!options.clutterFilter) {
    applyClutterBloom(reflectivity, seed);
  }
}

function applyBackgroundArtifacts(radarState, environment, options) {
  const { reflectivity, cc } = radarState;
  const { seed } = environment;
  for (let y = 0; y < GRID_SIZE; y++) {
    for (let x = 0; x < GRID_SIZE; x++) {
      const idx = y * GRID_SIZE + x;
      const range = Math.hypot(x - RADAR_ORIGIN.x, y - RADAR_ORIGIN.y);
      const attenuation = Math.exp(-range / 420);
      reflectivity[idx] *= attenuation + 0.3;
      reflectivity[idx] += (spatialNoise(x * 1.3, y * 1.1, seed) - 0.5) * 0.8;
      cc[idx] = Math.min(0.995, Math.max(0.4, cc[idx]));
    }
  }

  applyRadialDithering(reflectivity, seed, options.dealias);
}

function finalizeFields(radarState) {
  const { reflectivity, velocity, spectrumWidth } = radarState;
  for (let i = 0; i < reflectivity.length; i++) {
    reflectivity[i] = Math.max(0, reflectivity[i]);
    velocity[i] = clamp(velocity[i], -NYQUIST, NYQUIST);
    spectrumWidth[i] = Math.max(0.5, spectrumWidth[i]);
  }
}

function applyClutterBloom(field, seed) {
  const originX = Math.floor(RADAR_ORIGIN.x);
  const originY = Math.floor(RADAR_ORIGIN.y);
  for (let r = 2; r < 32; r++) {
    const ring = 2 * Math.PI * r;
    for (let n = 0; n < ring; n++) {
      const angle = (n / ring) * Math.PI * 2;
      const x = Math.round(originX + Math.cos(angle) * r);
      const y = Math.round(originY + Math.sin(angle) * r);
      if (x < 0 || x >= GRID_SIZE || y < 0 || y >= GRID_SIZE) continue;
      const idx = y * GRID_SIZE + x;
      const bloom = 20 + 6 * Math.sin(angle * 6) + (spatialNoise(x, y, seed) - 0.5) * 5;
      field[idx] = Math.max(field[idx], bloom);
    }
  }
}

function applyRadialDithering(field, seed, dealias) {
  const radialCount = 720;
  for (let az = 0; az < radialCount; az++) {
    const angle = (az / radialCount) * Math.PI * 2;
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    let previous = 0;
    for (let r = 0; r < GRID_SIZE * 0.85; r++) {
      const x = Math.floor(RADAR_ORIGIN.x + cos * r);
      const y = Math.floor(RADAR_ORIGIN.y + sin * r);
      if (x < 0 || x >= GRID_SIZE || y < 0 || y >= GRID_SIZE) break;
      const idx = y * GRID_SIZE + x;
      const gateNoise = spatialNoise(r * 0.75, az * 1.5, seed);
      const jitter = (gateNoise - 0.5) * 3.5;
      field[idx] = Math.max(0, field[idx] + jitter);
      if (!dealias && field[idx] < previous - 15) {
        field[idx] = previous - 10 * gateNoise;
      }
      previous = field[idx];
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

function spatialNoise(x, y, seed) {
  const value = Math.sin((x * 12.9898 + y * 78.233 + seed * 0.001) * 43758.5453);
  return value - Math.floor(value);
}
