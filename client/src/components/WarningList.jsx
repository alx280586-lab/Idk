function WarningList({ warnings, loading, error, selectedId, onSelect, onRefresh }) {
  return (
    <div className="panel warning-panel">
      <div className="warning-header">
        <h2>Active Warnings</h2>
        <button type="button" onClick={onRefresh} aria-label="Refresh warnings">
          ⟳
        </button>
      </div>
      {warnings.updated && (
        <p className="hint">Updated {new Date(warnings.updated).toLocaleTimeString()}</p>
      )}
      {loading && <p className="hint">Fetching warnings…</p>}
      {error && <p className="hint">Unable to load warnings.</p>}
      {warnings.features.length === 0 && !loading ? (
        <p className="hint">No active warnings.</p>
      ) : (
        <ul className="warning-list">
          {warnings.features.map((feature) => (
            <li
              key={feature.id}
              className={selectedId === feature.id ? 'active' : ''}
              style={{ borderLeftColor: feature.properties.color }}
            >
              <button type="button" onClick={() => onSelect(feature.id)}>
                <div className="warning-title">{feature.properties.event}</div>
                <div className="warning-meta">
                  <span>
                    {feature.properties.sent
                      ? new Date(feature.properties.sent).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit'
                        })
                      : '—'}
                  </span>
                  <span>→</span>
                  <span>
                    {feature.properties.expires
                      ? new Date(feature.properties.expires).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit'
                        })
                      : '—'}
                  </span>
                </div>
                <div className="warning-status">Status: {feature.properties.status}</div>
              </button>
              <a
                href={feature.properties.link}
                className="warning-link"
                target="_blank"
                rel="noreferrer"
              >
                Official text
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default WarningList;
