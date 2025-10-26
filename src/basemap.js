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

export function createBasemapTexture(gl) {
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
