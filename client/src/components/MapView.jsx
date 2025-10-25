import { useEffect, useRef } from 'react';
import L from 'leaflet';

function MapView({
  activeLayers,
  timelines,
  warnings,
  currentFrameIndex,
  selectedWarningId,
  onWarningFocus
}) {
  const mapRef = useRef(null);
  const radarLayerRefs = useRef(new Map());
  const warningsLayerRef = useRef(null);

  useEffect(() => {
    if (mapRef.current) return;
    const map = L.map('radar-map', {
      preferCanvas: true,
      zoomControl: true
    });
    map.setView([37.5, -97.5], 5);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 12,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    mapRef.current = map;
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const storedLayers = radarLayerRefs.current;

    // Remove layers that are no longer active.
    storedLayers.forEach((layer, key) => {
      if (!activeLayers.has(key)) {
        map.removeLayer(layer);
        storedLayers.delete(key);
      }
    });

    activeLayers.forEach((layerKey) => {
      const timeline = timelines[layerKey];
      if (!timeline || timeline.frames.length === 0) return;
      const frame =
        timeline.frames[currentFrameIndex] ?? timeline.frames[timeline.frames.length - 1];
      const timeParam = frame?.timeParameter ?? frame?.timestamp;

      const baseOptions = {
        layers: timeline.layerName,
        format: 'image/png',
        transparent: true,
        opacity: 0.6,
        time: timeParam,
        attribution: 'NOAA/NWS'
      };

      const existingLayer = storedLayers.get(layerKey);
      if (existingLayer) {
        existingLayer.setParams({ time: timeParam });
        if (!map.hasLayer(existingLayer)) {
          existingLayer.addTo(map);
        }
      } else {
        const layer = L.tileLayer.wms(timeline.serviceUrl, baseOptions);
        layer.addTo(map);
        storedLayers.set(layerKey, layer);
      }
    });
  }, [activeLayers, timelines, currentFrameIndex]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (warningsLayerRef.current) {
      warningsLayerRef.current.remove();
      warningsLayerRef.current = null;
    }

    if (!warnings || warnings.features.length === 0) return;

    const geoJsonLayer = L.geoJSON(warnings.features, {
      style: (feature) => ({
        color: feature.properties.color,
        weight: selectedWarningId === feature.id ? 4 : 2,
        fillOpacity: 0.2,
        opacity: 0.8
      }),
      onEachFeature: (feature, layer) => {
        layer.on('click', () => onWarningFocus(feature.id));
      }
    });

    geoJsonLayer.addTo(map);
    warningsLayerRef.current = geoJsonLayer;

    if (selectedWarningId) {
      const selectedLayer = geoJsonLayer.getLayers().find((layer) => layer.feature.id === selectedWarningId);
      if (selectedLayer) {
        map.fitBounds(selectedLayer.getBounds(), { maxZoom: 9, padding: [30, 30] });
      }
    }
  }, [warnings, selectedWarningId, onWarningFocus]);

  return <div id="radar-map" className="map" />;
}

export default MapView;
