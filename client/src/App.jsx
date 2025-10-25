import { useEffect, useMemo, useState } from 'react';

import MapView from './components/MapView.jsx';
import LayerToggles from './components/LayerToggles.jsx';
import LegendsPanel from './components/LegendsPanel.jsx';
import TimeControls from './components/TimeControls.jsx';
import WarningList from './components/WarningList.jsx';
import useRadarProducts from './hooks/useRadarProducts.js';
import useWarnings from './hooks/useWarnings.js';

const DEFAULT_ACTIVE_LAYERS = ['reflectivity'];

function App() {
  const [activeLayers, setActiveLayers] = useState(new Set(DEFAULT_ACTIVE_LAYERS));
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [selectedWarningId, setSelectedWarningId] = useState(null);

  const {
    timelines,
    legends,
    isLoading: radarLoading,
    error: radarError
  } = useRadarProducts();
  const {
    warnings,
    isLoading: warningsLoading,
    refresh,
    error: warningsError
  } = useWarnings();

  const maxFrames = useMemo(() => {
    const longest = Math.max(
      0,
      ...Object.values(timelines).map((timeline) => timeline.frames.length)
    );
    return longest;
  }, [timelines]);

  const currentTimestamp = useMemo(() => {
    const firstActiveLayer = Array.from(activeLayers)[0];
    if (!firstActiveLayer) return null;
    const timeline = timelines[firstActiveLayer];
    if (!timeline) return null;
    return timeline.frames[currentFrameIndex]?.timestamp ?? timeline.lastUpdated;
  }, [activeLayers, timelines, currentFrameIndex]);

  const handleToggleLayer = (layerKey) => {
    setActiveLayers((prev) => {
      const next = new Set(prev);
      if (next.has(layerKey)) {
        next.delete(layerKey);
      } else {
        next.add(layerKey);
      }
      if (next.size === 0) {
        next.add(layerKey);
      }
      return next;
    });
  };

  const handleFrameChange = (value) => {
    setCurrentFrameIndex(Number(value));
  };

  useEffect(() => {
    if (!isPlaying) return undefined;
    const interval = window.setInterval(() => {
      setCurrentFrameIndex((prev) => {
        const maxIndex = Math.max(maxFrames - 1, 0);
        if (maxIndex <= 0) return 0;
        const next = prev + 1;
        return next > maxIndex ? 0 : next;
      });
    }, 750);
    return () => window.clearInterval(interval);
  }, [isPlaying, maxFrames]);

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <header>
          <h1>Weather Radar Looker</h1>
          <p className="timestamp">
            Latest update: {currentTimestamp ? new Date(currentTimestamp).toLocaleString() : '—'}
          </p>
        </header>
        <section>
          <LayerToggles
            activeLayers={activeLayers}
            onToggle={handleToggleLayer}
            isLoading={radarLoading}
            error={radarError}
          />
        </section>
        <section className="warnings-section">
          <WarningList
            warnings={warnings}
            loading={warningsLoading}
            error={warningsError}
            selectedId={selectedWarningId}
            onSelect={(id) => setSelectedWarningId(id)}
            onRefresh={refresh}
          />
        </section>
      </aside>
      <main className="map-container">
        <MapView
          activeLayers={activeLayers}
          timelines={timelines}
          legends={legends}
          warnings={warnings}
          currentFrameIndex={currentFrameIndex}
          selectedWarningId={selectedWarningId}
          onWarningFocus={(id) => setSelectedWarningId(id)}
        />
        <div className="map-overlays">
          <TimeControls
            currentFrameIndex={currentFrameIndex}
            maxFrames={Math.max(maxFrames - 1, 0)}
            isPlaying={isPlaying}
            onFrameChange={handleFrameChange}
            onPlayToggle={() => setIsPlaying((prev) => !prev)}
            onStep={(direction) => {
              setCurrentFrameIndex((prev) => {
                const next = prev + direction;
                const maxIndex = Math.max(maxFrames - 1, 0);
                if (next < 0) return maxIndex;
                if (next > maxIndex) return 0;
                return next;
              });
            }}
          />
          <LegendsPanel activeLayers={activeLayers} legends={legends} />
        </div>
      </main>
    </div>
  );
}

export default App;
