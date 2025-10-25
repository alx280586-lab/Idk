function TimeControls({
  currentFrameIndex,
  maxFrames,
  isPlaying,
  onFrameChange,
  onPlayToggle,
  onStep
}) {
  return (
    <div className="time-controls">
      <div className="buttons">
        <button type="button" onClick={() => onStep(-1)} aria-label="Previous frame">
          ◀
        </button>
        <button type="button" onClick={onPlayToggle} aria-label="Play/Pause loop">
          {isPlaying ? 'Pause' : 'Play'}
        </button>
        <button type="button" onClick={() => onStep(1)} aria-label="Next frame">
          ▶
        </button>
      </div>
      <input
        type="range"
        min="0"
        max={maxFrames}
        value={currentFrameIndex}
        onChange={(event) => onFrameChange(event.target.value)}
      />
      <div className="range-labels">
        <span>Past</span>
        <span>Latest</span>
      </div>
    </div>
  );
}

export default TimeControls;
