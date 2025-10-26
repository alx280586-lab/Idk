import { createBasemapTexture } from "./basemap.js";
import { COLOR_TABLES, getLegendRange } from "./colorTables.js";
import { Radar } from "./radar.js";

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
  float dist = distance(v_uv, vec2(${Radar.RADAR_ORIGIN.x / Radar.GRID_SIZE}.0, ${Radar.RADAR_ORIGIN.y / Radar.GRID_SIZE}.0));
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

export function createRenderer(canvas) {
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

export function updateColorRamp(renderer, product) {
  renderer.currentProduct = product;
  const { ramp } = COLOR_TABLES[product];
  renderer.rampBuffer.set(ramp);
  const { gl, colorRampTexture } = renderer;
  gl.bindTexture(gl.TEXTURE_2D, colorRampTexture);
  gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 256, 1, gl.RGBA, gl.FLOAT, renderer.rampBuffer);
  drawLegend(renderer, product);
}

export function drawLegend(renderer, product) {
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

export function uploadField(renderer, field) {
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

export function renderFrame(renderer, options) {
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

export function resizeRenderer(renderer) {
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

export const Renderer = {
  create: createRenderer,
  updateRamp: updateColorRamp,
  uploadField,
  render: renderFrame,
  resize: resizeRenderer,
  drawLegend
};
