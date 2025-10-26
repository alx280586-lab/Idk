(function (global) {
  'use strict';
  const modules = {
    './alerts.js': function (module, exports, require) {
      const {Radar} = require("./radar.js");
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
      
      function createAlerts() {
        return {
          active: [],
          history: []
        };
      }
      
      function updateAlerts(alerts, radarState, storms, timeMinutes, options) {
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
      
        if (
          storm.phase === "rotation" &&
          storm.ageMinutes > 90 &&
          hasCouplet &&
          minCC < 0.8 &&
          Math.random() > options.falseAlarm * 0.25
        ) {
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
      
        if ((maxRefl > 60 || hailSignal) && storm.ageMinutes > 45) {
          const warning = { ...baseWarning };
          warning.type = hailSignal ? "severePds" : "severe";
          warning.headline = hailSignal
            ? "PDS SEVERE THUNDERSTORM – VERY LARGE HAIL"
            : "SEVERE THUNDERSTORM – 60 KT WINDS";
          warning.expires = timeMinutes + 45;
          warnings.push(warning);
        }
      
        if (storm.type === "tropical" && storm.ageMinutes > 120 && maxRefl > 45 && Math.random() > options.falseAlarm * 0.5) {
          const warning = { ...baseWarning };
          warning.type = "flashFlood";
          warning.headline = "FLASH FLOOD WARNING – TRAINING RAINBANDS";
          warning.expires = timeMinutes + 60;
          warnings.push(warning);
        }
      
        if (storm.phase === "decay" && storm.ageMinutes > 150 && attrs.zdrMean < 0.5 && minCC > 0.95) {
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
      
      function renderWarnings(ctx, warnings, alphaPulse, projection) {
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
      
      const Alerts = {
        create: createAlerts,
        update: updateAlerts,
        render: renderWarnings
      };
      
      exports.Alerts = Alerts;
      exports.createAlerts = createAlerts;
      exports.updateAlerts = updateAlerts;
      exports.renderWarnings = renderWarnings;
    },
    './analyst.js': function (module, exports, require) {
      function createAnalyst() {
        return {
          elapsed: 0,
          cadence: 10,
          log: []
        };
      }
      
      function updateAnalyst(analyst, storms, timeMinutes, logEl) {
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
      
      const Analyst = {
        create: createAnalyst,
        update: updateAnalyst
      };
      
      exports.Analyst = Analyst;
      exports.createAnalyst = createAnalyst;
      exports.updateAnalyst = updateAnalyst;
    },
    './atmo.js': function (module, exports, require) {
      const GRID_SIZE = 512;
      const CELL_KM = 5;
      const DAY_MINUTES = 1440;
      
      function createRandom(seed) {
        let state = seed >>> 0;
        return () => {
          state = Math.imul(state ^ (state >>> 15), 1 | state);
          state = state + Math.imul(state ^ (state >>> 7), 61 | state);
          return ((state ^ (state >>> 14)) >>> 0) / 4294967296;
        };
      }
      
      function createAtmo(seed = 0x1337c0de) {
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
      
      function updateAtmosphere(state, dtMinutes, options) {
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
      
      const Atmosphere = {
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
      
      exports.Atmosphere = Atmosphere;
      exports.createRandom = createRandom;
      exports.createAtmo = createAtmo;
      exports.updateAtmosphere = updateAtmosphere;
    },
    './basemap.js': function (module, exports, require) {
      const WIDTH = 1024;
      const HEIGHT = 512;
      
      function seededRandom(seed) {
        let x = seed >>> 0;
        return () => {
          x = (x ^ (x << 13)) >>> 0;
          x = (x ^ (x >>> 17)) >>> 0;
          x = (x ^ (x << 5)) >>> 0;
          return (x & 0xffffffff) / 0xffffffff;
        };
      }
      
      function drawLandMask(rand) {
        const data = new Uint8ClampedArray(WIDTH * HEIGHT * 4);
        for (let y = 0; y < HEIGHT; y++) {
          for (let x = 0; x < WIDTH; x++) {
            const u = x / WIDTH;
            const v = y / HEIGHT;
            let coast = Math.exp(-Math.pow((u - 0.45) * 5, 2) - Math.pow((v - 0.55) * 6, 2));
            coast += 0.3 * Math.exp(-Math.pow((u - 0.25) * 4, 2) - Math.pow((v - 0.4) * 5, 2));
            coast += 0.2 * Math.exp(-Math.pow((u - 0.7) * 4, 2) - Math.pow((v - 0.45) * 6, 2));
            coast = Math.min(1, coast * 1.5);
            const terrain = coast + 0.2 * (rand() - 0.5);
            const shading = 0.6 + 0.4 * Math.cos((x / WIDTH) * Math.PI) * Math.sin((y / HEIGHT) * Math.PI);
            let r = 40 + 80 * terrain;
            let g = 70 + 90 * terrain + 20 * shading;
            let b = 50 + 60 * terrain;
            if (terrain < 0.15) {
              r = 40;
              g = 60 + 30 * shading;
              b = 120 + 40 * shading;
            }
            const idx = (y * WIDTH + x) * 4;
            data[idx] = r;
            data[idx + 1] = g;
            data[idx + 2] = b;
            data[idx + 3] = 255;
          }
        }
        return data;
      }
      
      function createBasemapTexture(gl) {
        const rand = seededRandom(0x5eed);
        const data = drawLandMask(rand);
        const tex = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, tex);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.texImage2D(
          gl.TEXTURE_2D,
          0,
          gl.RGBA,
          WIDTH,
          HEIGHT,
          0,
          gl.RGBA,
          gl.UNSIGNED_BYTE,
          data
        );
        return { texture: tex, width: WIDTH, height: HEIGHT };
      }
      
      exports.createBasemapTexture = createBasemapTexture;
    },
    './colorTables.js': function (module, exports, require) {
      const COLOR_TABLES = {
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
      
      function getLegendRange(product) {
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
      
      exports.COLOR_TABLES = COLOR_TABLES;
      exports.getLegendRange = getLegendRange;
    },
    './radar.js': function (module, exports, require) {
      const GRID_SIZE = 512;
      const RADAR_ORIGIN = { x: GRID_SIZE * 0.45, y: GRID_SIZE * 0.55 };
      const NYQUIST = 63;
      
      function createRadarState() {
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
      
      function generateFields(radarState, atmoState, options) {
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
      
      function blendFields(current, next, t) {
        const keys = ["reflectivity", "velocity", "spectrumWidth", "cc", "zdr", "kdp"];
        for (const key of keys) {
          const a = current[key];
          const b = next[key];
          for (let i = 0; i < a.length; i++) {
            a[i] = a[i] * (1 - t) + b[i] * t;
          }
        }
      }
      
      const Radar = {
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
      
      exports.Radar = Radar;
      exports.createRadarState = createRadarState;
      exports.generateFields = generateFields;
      exports.blendFields = blendFields;
    },
    './renderer.js': function (module, exports, require) {
      const {createBasemapTexture} = require("./basemap.js");
      const {COLOR_TABLES,getLegendRange} = require("./colorTables.js");
      const {Radar} = require("./radar.js");
      const VERTEX_SHADER = `#version 300 es
      precision highp float;
      in vec2 a_position;
      out vec2 v_uv;
      void main() {
        v_uv = (a_position + 1.0) * 0.5;
        gl_Position = vec4(a_position, 0.0, 1.0);
      }`;
      
      const FRAGMENT_SHADER = `#version 300 es
      precision highp float;
      precision highp sampler2D;
      
      in vec2 v_uv;
      out vec4 outColor;
      
      uniform sampler2D uData;
      uniform sampler2D uColorRamp;
      uniform sampler2D uBasemap;
      uniform vec2 uRange;
      uniform float uBrightness;
      uniform float uContrast;
      uniform float uGamma;
      uniform float uBeamWidth;
      uniform float uTime;
      uniform float uNightFactor;
      uniform int uProduct;
      uniform float uColorBlind;
      
      vec3 applyColorBlind(vec3 color) {
        // simple matrix approximating deuteranopia-safe palette
        mat3 mat = mat3(
          0.625, 0.375, 0.0,
          0.7, 0.3, 0.0,
          0.0, 0.3, 0.7
        );
        return clamp(mat * color, 0.0, 1.0);
      }
      
      void main() {
        float value = texture(uData, v_uv).r;
        float norm = clamp((value - uRange.x) / (uRange.y - uRange.x), 0.0, 1.0);
        vec4 rampColor = texture(uColorRamp, vec2(norm, 0.5));
        vec4 base = texture(uBasemap, v_uv);
        float dist = distance(v_uv, vec2(${Radar.RADAR_ORIGIN.x / Radar.GRID_SIZE}, ${Radar.RADAR_ORIGIN.y / Radar.GRID_SIZE}));
        float beam = smoothstep(0.0, 0.8, dist);
        float attenuation = exp(-dist * 2.5);
        float ring = sin(dist * 80.0 + uTime * 0.2) * 0.004;
        vec3 shadedBase = base.rgb * mix(1.2, 0.6, uNightFactor) + ring;
        vec3 productColor = rampColor.rgb;
      
        if (uProduct == 1) {
          // velocity color-blind friendly alternate ramp (blue-orange)
          productColor = mix(vec3(0.1, 0.3, 0.8), vec3(0.9, 0.45, 0.2), norm);
        }
      
        float brightness = uBrightness + (0.3 * (1.0 - attenuation));
        float contrast = uContrast + beam * uBeamWidth * 0.6;
        vec3 color = productColor;
        if (uColorBlind > 0.5) {
          color = applyColorBlind(color);
        }
        color = pow(color, vec3(uGamma));
        color = (color - 0.5) * contrast + 0.5;
        color *= brightness;
        float alpha = clamp(norm * 1.4, 0.0, 1.0);
        alpha = mix(alpha, alpha * attenuation, 0.5);
        outColor = vec4(mix(shadedBase, color, alpha), 1.0);
      }`;
      
      function createRenderer(canvas) {
        const gl = canvas.getContext("webgl2", { antialias: false });
        if (!gl) throw new Error("WebGL2 not supported");
      
        const program = createProgram(gl, VERTEX_SHADER, FRAGMENT_SHADER);
        const vao = gl.createVertexArray();
        gl.bindVertexArray(vao);
        const quad = new Float32Array([
          -1, -1,
          1, -1,
          -1, 1,
          -1, 1,
          1, -1,
          1, 1
        ]);
        const vbo = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
        gl.bufferData(gl.ARRAY_BUFFER, quad, gl.STATIC_DRAW);
        const loc = gl.getAttribLocation(program, "a_position");
        gl.enableVertexAttribArray(loc);
        gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
      
        const dataTexture = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, dataTexture);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.texImage2D(
          gl.TEXTURE_2D,
          0,
          gl.R32F,
          Radar.GRID_SIZE,
          Radar.GRID_SIZE,
          0,
          gl.RED,
          gl.FLOAT,
          null
        );
      
        const colorRampTexture = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, colorRampTexture);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32F, 256, 1, 0, gl.RGBA, gl.FLOAT, null);
      
        const basemap = createBasemapTexture(gl);
      
        const uniforms = getUniformLocations(gl, program, [
          "uData",
          "uColorRamp",
          "uBasemap",
          "uRange",
          "uBrightness",
          "uContrast",
          "uGamma",
          "uBeamWidth",
          "uTime",
          "uNightFactor",
          "uProduct",
          "uColorBlind"
        ]);
      
        gl.useProgram(program);
        gl.uniform1i(uniforms.uData, 0);
        gl.uniform1i(uniforms.uColorRamp, 1);
        gl.uniform1i(uniforms.uBasemap, 2);
        gl.uniform1f(uniforms.uColorBlind, 0.0);
      
        const state = {
          gl,
          program,
          vao,
          dataTexture,
          colorRampTexture,
          basemap,
          currentProduct: "reflectivity",
          legendCanvas: document.getElementById("legend-gradient"),
          colorBlindMode: false,
          brightness: 1,
          contrast: 1,
          gamma: 1,
          beamWidth: 0.3,
          nightFactor: 0,
          rampBuffer: new Float32Array(256 * 4),
          dataBuffer: new Float32Array(Radar.GRID_SIZE * Radar.GRID_SIZE),
          uniforms
        };
      
        updateColorRamp(state, "reflectivity");
        drawLegend(state, "reflectivity");
        return state;
      }
      
      function updateColorRamp(renderer, product) {
        renderer.currentProduct = product;
        const { ramp } = COLOR_TABLES[product];
        renderer.rampBuffer.set(ramp);
        const { gl, colorRampTexture } = renderer;
        gl.bindTexture(gl.TEXTURE_2D, colorRampTexture);
        gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 256, 1, gl.RGBA, gl.FLOAT, renderer.rampBuffer);
        drawLegend(renderer, product);
      }
      
      function drawLegend(renderer, product) {
        const canvas = renderer.legendCanvas;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        const { ramp } = COLOR_TABLES[product];
        const image = ctx.createImageData(canvas.width, canvas.height);
        for (let y = 0; y < canvas.height; y++) {
          const t = 1 - y / (canvas.height - 1);
          const idx = Math.floor(t * 255);
          const r = Math.floor(ramp[idx * 4] * 255);
          const g = Math.floor(ramp[idx * 4 + 1] * 255);
          const b = Math.floor(ramp[idx * 4 + 2] * 255);
          for (let x = 0; x < canvas.width; x++) {
            const offset = (y * canvas.width + x) * 4;
            image.data[offset] = r;
            image.data[offset + 1] = g;
            image.data[offset + 2] = b;
            image.data[offset + 3] = 255;
          }
        }
        ctx.putImageData(image, 0, 0);
        document.querySelector("#legend .legend-title").textContent = getLegendRange(product).units;
      }
      
      function uploadField(renderer, field) {
        const { gl, dataTexture } = renderer;
        renderer.dataBuffer.set(field);
        gl.bindTexture(gl.TEXTURE_2D, dataTexture);
        gl.texSubImage2D(
          gl.TEXTURE_2D,
          0,
          0,
          0,
          Radar.GRID_SIZE,
          Radar.GRID_SIZE,
          gl.RED,
          gl.FLOAT,
          renderer.dataBuffer
        );
      }
      
      function renderFrame(renderer, options) {
        const { gl, program, vao, basemap, uniforms } = renderer;
        gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
        gl.clearColor(0, 0, 0, 1);
        gl.clear(gl.COLOR_BUFFER_BIT);
      
        const { min, max } = getLegendRange(renderer.currentProduct);
        gl.useProgram(program);
        gl.bindVertexArray(vao);
      
        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, renderer.dataTexture);
        gl.activeTexture(gl.TEXTURE1);
        gl.bindTexture(gl.TEXTURE_2D, renderer.colorRampTexture);
        gl.activeTexture(gl.TEXTURE2);
        gl.bindTexture(gl.TEXTURE_2D, basemap.texture);
      
        gl.uniform2f(uniforms.uRange, min, max);
        gl.uniform1f(uniforms.uBrightness, renderer.brightness);
        gl.uniform1f(uniforms.uContrast, renderer.contrast);
        gl.uniform1f(uniforms.uGamma, renderer.gamma);
        gl.uniform1f(uniforms.uBeamWidth, renderer.beamWidth);
        gl.uniform1f(uniforms.uTime, options.time);
        gl.uniform1f(uniforms.uNightFactor, renderer.nightFactor);
        gl.uniform1i(uniforms.uProduct, productIndex(renderer.currentProduct));
        gl.uniform1f(uniforms.uColorBlind, renderer.colorBlindMode ? 1 : 0);
      
        gl.drawArrays(gl.TRIANGLES, 0, 6);
      }
      
      function resizeRenderer(renderer) {
        const { gl } = renderer;
        const displayWidth = gl.canvas.clientWidth;
        const displayHeight = gl.canvas.clientHeight;
        if (gl.canvas.width !== displayWidth || gl.canvas.height !== displayHeight) {
          gl.canvas.width = displayWidth;
          gl.canvas.height = displayHeight;
        }
      }
      
      function productIndex(product) {
        switch (product) {
          case "velocity":
            return 1;
          case "spectrumWidth":
            return 2;
          case "cc":
            return 3;
          case "zdr":
            return 4;
          case "kdp":
            return 5;
          default:
            return 0;
        }
      }
      
      function createShader(gl, type, source) {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
          throw new Error(gl.getShaderInfoLog(shader));
        }
        return shader;
      }
      
      function createProgram(gl, vertSrc, fragSrc) {
        const vert = createShader(gl, gl.VERTEX_SHADER, vertSrc);
        const frag = createShader(gl, gl.FRAGMENT_SHADER, fragSrc);
        const program = gl.createProgram();
        gl.attachShader(program, vert);
        gl.attachShader(program, frag);
        gl.linkProgram(program);
        if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
          throw new Error(gl.getProgramInfoLog(program));
        }
        return program;
      }
      
      function getUniformLocations(gl, program, names) {
        const map = {};
        for (const name of names) {
          map[name] = gl.getUniformLocation(program, name);
        }
        return map;
      }
      
      const Renderer = {
        create: createRenderer,
        updateRamp: updateColorRamp,
        uploadField,
        render: renderFrame,
        resize: resizeRenderer,
        drawLegend
      };
      
      exports.Renderer = Renderer;
      exports.createRenderer = createRenderer;
      exports.updateColorRamp = updateColorRamp;
      exports.drawLegend = drawLegend;
      exports.uploadField = uploadField;
      exports.renderFrame = renderFrame;
      exports.resizeRenderer = resizeRenderer;
    },
    './ui.js': function (module, exports, require) {
      const {Renderer} = require("./renderer.js");
      const {getLegendRange} = require("./colorTables.js");
      function setupUI(state) {
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
      
      const UI = {
        setup: setupUI
      };
      
      exports.UI = UI;
      exports.setupUI = setupUI;
    },
    './main.js': function (module, exports, require) {
      const {Atmosphere} = require("./atmo.js");
      const {Radar} = require("./radar.js");
      const {Renderer} = require("./renderer.js");
      const {Alerts} = require("./alerts.js");
      const {Analyst} = require("./analyst.js");
      const {UI} = require("./ui.js");
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
    }
  };

  const cache = {};

  function require(id) {
    if (cache[id]) {
      return cache[id].exports;
    }
    const factory = modules[id];
    if (!factory) {
      throw new Error('Cannot find module: ' + id);
    }
    const module = { exports: {} };
    cache[id] = module;
    factory(module, module.exports, require);
    return module.exports;
  }

  global.SyntheticRadar = global.SyntheticRadar || {};

  global.SyntheticRadar.require = require;

  global.SyntheticRadar.modules = Object.keys(modules);

  require('./main.js');

})(typeof globalThis !== 'undefined' ? globalThis : window);
