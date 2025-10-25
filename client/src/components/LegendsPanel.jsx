function LegendsPanel({ activeLayers, legends }) {
  return (
    <div className="legends-panel">
      {Array.from(activeLayers).map((layerKey) => {
        const legend = legends[layerKey];
        if (!legend) return null;
        return (
          <div className="legend" key={layerKey}>
            <h3>{legend.title}</h3>
            <p className="legend-units">Units: {legend.units}</p>
            <div className="legend-ramp">
              {legend.colorRamp.map((color, index) => (
                <span
                  key={color + index}
                  style={{ backgroundColor: color }}
                  title={color}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default LegendsPanel;
