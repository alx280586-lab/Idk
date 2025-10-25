const LAYER_LABELS = {
  reflectivity: 'Reflectivity (dBZ)',
  velocity: 'Velocity (kts)',
  correlationCoefficient: 'Correlation Coefficient',
  echoTops: 'Echo Tops (kft)'
};

function LayerToggles({ activeLayers, onToggle, isLoading, error }) {
  return (
    <div className="panel">
      <h2>Radar Layers</h2>
      {isLoading && <p className="hint">Loading radar metadata…</p>}
      {error && <p className="hint">Failed to load radar products.</p>}
      <ul className="layer-list">
        {Object.entries(LAYER_LABELS).map(([key, label]) => (
          <li key={key}>
            <label>
              <input
                type="checkbox"
                checked={activeLayers.has(key)}
                onChange={() => onToggle(key)}
              />
              <span>{label}</span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default LayerToggles;
