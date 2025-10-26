export const COLOR_TABLES = {
  reflectivity: createRamp([
    { v: 0, c: [0, 0.0627, 0] },
    { v: 5, c: [0, 0.168, 0] },
    { v: 10, c: [0.0078, 0.298, 0.0078] },
    { v: 20, c: [0.0588, 0.5137, 0.0588] },
    { v: 30, c: [0.4, 0.749, 0.078] },
    { v: 40, c: [0.894, 0.925, 0.058] },
    { v: 45, c: [1, 0.8, 0.039] },
    { v: 50, c: [0.992, 0.585, 0.02] },
    { v: 55, c: [0.945, 0.305, 0.066] },
    { v: 60, c: [0.878, 0.082, 0.082] },
    { v: 65, c: [0.75, 0, 0.2] },
    { v: 70, c: [0.537, 0, 0.596] },
    { v: 75, c: [0.925, 0.949, 0.925] }
  ], 0, 80),
  velocity: createRamp([
    { v: -63, c: [0, 0.2, 0.3] },
    { v: -50, c: [0, 0.4, 0.4] },
    { v: -25, c: [0.1, 0.7, 0.1] },
    { v: 0, c: [0.1, 0.1, 0.1] },
    { v: 25, c: [0.8, 0.2, 0.1] },
    { v: 50, c: [0.85, 0.35, 0.35] },
    { v: 63, c: [0.95, 0.7, 0.7] }
  ], -63, 63),
  spectrumWidth: createRamp([
    { v: 0, c: [0, 0, 0.2] },
    { v: 10, c: [0.3, 0.1, 0.5] },
    { v: 30, c: [0.8, 0.2, 0.7] },
    { v: 60, c: [1, 1, 1] }
  ], 0, 60),
  cc: createRamp([
    { v: 0.5, c: [0.1, 0.3, 0.6] },
    { v: 0.7, c: [0.15, 0.65, 0.8] },
    { v: 0.8, c: [0.4, 0.8, 0.9] },
    { v: 0.9, c: [0.9, 0.7, 0.5] },
    { v: 1.0, c: [1, 0.95, 0.95] }
  ], 0.5, 1.0),
  zdr: createRamp([
    { v: -1, c: [0.5, 0.2, 0.7] },
    { v: 0, c: [0.2, 0.4, 0.6] },
    { v: 1, c: [0.4, 0.7, 0.9] },
    { v: 2, c: [0.9, 0.8, 0.3] },
    { v: 3.5, c: [1, 0.5, 0.1] }
  ], -1, 4),
  kdp: createRamp([
    { v: 0, c: [0.2, 0.2, 0.3] },
    { v: 1, c: [0.3, 0.5, 0.8] },
    { v: 3, c: [0.6, 0.7, 0.1] },
    { v: 5, c: [1, 0.3, 0.1] }
  ], 0, 5)
};

export function getLegendRange(product) {
  switch (product) {
    case "reflectivity":
      return { min: 0, max: 80, units: "dBZ" };
    case "velocity":
      return { min: -63, max: 63, units: "kt" };
    case "spectrumWidth":
      return { min: 0, max: 60, units: "kt" };
    case "cc":
      return { min: 0.5, max: 1, units: "CC" };
    case "zdr":
      return { min: -1, max: 4, units: "dB" };
    case "kdp":
      return { min: 0, max: 5, units: "°/km" };
    default:
      return { min: 0, max: 1, units: "" };
  }
}

function createRamp(stops, min, max) {
  const ramp = new Float32Array(256 * 4);
  for (let i = 0; i < 256; i++) {
    const v = min + ((max - min) * i) / 255;
    for (let s = 0; s < stops.length - 1; s++) {
      const a = stops[s];
      const b = stops[s + 1];
      if (v >= a.v && v <= b.v) {
        const t = (v - a.v) / (b.v - a.v);
        const color = [
          lerp(a.c[0], b.c[0], t),
          lerp(a.c[1], b.c[1], t),
          lerp(a.c[2], b.c[2], t),
          1
        ];
        ramp.set(color, i * 4);
        break;
      }
    }
  }
  return { ramp, min, max };
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}
