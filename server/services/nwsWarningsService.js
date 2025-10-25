import fetch from 'node-fetch';

import { WARNINGS_URL } from '../config.js';

const WARNING_TYPE_COLORS = {
  TornadoWarning: '#ff3b30',
  SevereThunderstormWarning: '#ffd60a',
  FlashFloodWarning: '#64d2ff'
};

export async function fetchActiveWarnings(status = 'actual') {
  const url = new URL(WARNINGS_URL);
  if (status) {
    url.searchParams.set('status', status);
  }
  url.searchParams.set('message_type', 'alert');
  url.searchParams.set('format', 'geojson');

  const response = await fetch(url.toString(), {
    headers: {
      'User-Agent': 'Weather Radar Visualizer (demo contact@example.com)',
      Accept: 'application/geo+json'
    }
  });

  if (!response.ok) {
    throw new Error(`Failed to load NWS warnings: ${response.status}`);
  }

  const geojson = await response.json();
  const features = (geojson.features ?? []).map((feature) => {
    const { properties, geometry } = feature;
    const color = WARNING_TYPE_COLORS[properties.event] ?? '#ff9f0a';
    return {
      id: feature.id,
      geometry,
      properties: {
        event: properties.event,
        headline: properties.headline,
        sent: properties.sent,
        effective: properties.effective,
        onset: properties.onset,
        expires: properties.expires,
        ends: properties.ends,
        severity: properties.severity,
        certainty: properties.certainty,
        urgency: properties.urgency,
        description: properties.description,
        instruction: properties.instruction,
        nwsHeadline: properties.parameters?.NWSheadline?.[0],
        color,
        status: properties.status,
        source: properties.senderName,
        link: properties.links?.[0]?.href ?? properties['@id']
      }
    };
  });

  return {
    type: geojson.type,
    updated: geojson.updated ?? new Date().toISOString(),
    features
  };
}
