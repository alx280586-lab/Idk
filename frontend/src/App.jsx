import React from 'react';

import AutomationPanel from './components/AutomationPanel';
import ClipStatusViewer from './components/ClipStatusViewer';
import Header from './components/Header';
import SchedulingForm from './components/SchedulingForm';
import TrendHighlights from './components/TrendHighlights';
import UploadForm from './components/UploadForm';
import VideoAnalytics from './components/VideoAnalytics';

const App = () => {
  return (
    <div className="app-shell">
      <Header />
      <main className="main-grid">
        <section className="panel">
          <h2>Generate New Clips</h2>
          <UploadForm />
        </section>
        <section className="panel">
          <h2>Clip Status &amp; Uploads</h2>
          <ClipStatusViewer />
        </section>
        <section className="panel">
          <h2>Smart Scheduling</h2>
          <SchedulingForm />
        </section>
        <section className="panel wide">
          <h2>Performance Intelligence</h2>
          <VideoAnalytics />
        </section>
        <section className="panel">
          <h2>Trending Boosters</h2>
          <TrendHighlights />
        </section>
        <section className="panel">
          <h2>Autonomous Mode</h2>
          <AutomationPanel />
        </section>
      </main>
    </div>
  );
};

export default App;
