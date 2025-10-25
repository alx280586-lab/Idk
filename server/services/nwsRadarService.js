import fetch from 'node-fetch';

import {
  RADAR_FRAME_COUNT,
  RADAR_FRAME_INTERVAL_MINUTES,
  RADAR_PRODUCTS,
  RADAR_TILE_BASE_URL
} from '../config.js';
import { minutesAgo } from '../utils/timeUtils.js';

const LEGENDS = {
  reflectivity: {
    title: 'Composite Reflectivity',
    units: 'dBZ',
    colorRamp: [
      '#ffffff',
      '#c8ffff',
      '#64f5ff',
      '#00e1ff',
      '#00ccff',
      '#00ff00',
      '#32cd32',
      '#ffff00',
      '#ffc800',
      '#ff9600',
      '#ff0000',
      '#c80000',
      '#960000',
      '#ff00ff'
    ]
  },
  velocity: {
    title: 'Radial Velocity',
    units: 'kts',
    colorRamp: [
      '#8300a9',
      '#b300d9',
      '#d900ff',
      '#ff00ff',
      '#ff78ff',
      '#ffb4ff',
      '#ffffff',
      '#c0ffc0',
      '#78ff78',
      '#00ff00',
      '#00d966',
      '#00a99d',
      '#0078ff',
      '#0046ff'
    ]
  },
  correlationCoefficient: {
    title: 'Correlation Coefficient',
    units: 'unitless',
    colorRamp: [
      '#4d004b',
      '#810f7c',
      '#8c6bb1',
      '#9ebcda',
      '#c7e9b4',
      '#edf8fb',
      '#ffffcc'
    ]
  },
  echoTops: {
    title: 'Echo Tops',
    units: 'kft',
    colorRamp: [
      '#00429d',
      '#4771b2',
      '#73a2c6',
      '#a5d5d8',
      '#ffffe0',
      '#ffbc80',
      '#d1495b'
    ]
  }
};

export function getLegendForProduct(productKey) {
  return LEGENDS[productKey];
}

export async function buildRadarTimeline(productKey) {
  const layerName = RADAR_PRODUCTS[productKey];
  if (!layerName) {
    throw new Error(`Unsupported radar product: ${productKey}`);
  }

  const frames = [];
  const now = new Date();
  for (let i = RADAR_FRAME_COUNT - 1; i >= 0; i -= 1) {
    const timestamp = minutesAgo(now, i * RADAR_FRAME_INTERVAL_MINUTES);
    frames.push({
      timestamp: timestamp.toISOString(),
      timeParameter: timestamp.toISOString()
    });
  }

  const serviceUrl = RADAR_TILE_BASE_URL.replace('{product}', layerName);

  // Optionally validate the WMS endpoint so failures surface early.
  try {
    const capabilitiesUrl = `${serviceUrl}?service=WMS&request=GetCapabilities`;
    await fetch(capabilitiesUrl, { method: 'HEAD' });
  } catch (error) {
    console.warn(`Warning: unable to validate WMS endpoint for ${productKey}`, error);
  }

  return {
    productKey,
    layerName,
    serviceUrl,
    requestType: 'WMS',
    frames,
    lastUpdated: now.toISOString()
  };
}
