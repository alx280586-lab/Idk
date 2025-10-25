import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import api from '../hooks/useApi';

const ClipStatusViewer = () => {
  const [taskId, setTaskId] = useState('');
  const [status, setStatus] = useState(null);

  const mutation = useMutation({
    mutationFn: async (id) => {
      const { data } = await api.get(`/videos/${id}`);
      return data;
    },
    onSuccess: (data) => setStatus(data),
  });

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!taskId) return;
    mutation.mutate(taskId);
  };

  return (
    <div>
      <form className="form inline" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Enter task id"
          value={taskId}
          onChange={(event) => setTaskId(event.target.value)}
        />
        <button type="submit" disabled={mutation.isLoading}>
          {mutation.isLoading ? 'Loading…' : 'Lookup task'}
        </button>
      </form>

      {status && (
        <div className="status-grid">
          <div className="card">
            <h3>Task Overview</h3>
            <p>
              <strong>Status:</strong> {status.status}
            </p>
            <p>
              <strong>Clips generated:</strong> {status.clips ? status.clips.length : 0}
            </p>
          </div>
          {status.most_watched && (
            <div className="card">
              <h3>Most Watched Moment</h3>
              <p className="timestamp">
                {Number(status.most_watched.start || 0).toFixed(1)}s –
                {` ${Number(status.most_watched.end || 0).toFixed(1)}s`}
              </p>
              <p className="moment-text">“{status.most_watched.text}”</p>
              <p className="metric">
                Predicted viewer retention:{' '}
                {Number((status.most_watched.viewer_retention || 0) * 100).toFixed(0)}%
              </p>
            </div>
          )}
        </div>
      )}

      {status?.clips && (
        <div className="card wide">
          <h3>Auto-Published Clips</h3>
          <table>
            <thead>
              <tr>
                <th>Clip ID</th>
                <th>Aspect</th>
                <th>Duration</th>
                <th>Platform</th>
                <th>Status</th>
                <th>Published</th>
              </tr>
            </thead>
            <tbody>
              {status.clips.flatMap((clip) =>
                (clip.uploads || []).map((upload) => (
                  <tr key={`${clip.clip_id}-${upload.platform}`}>
                    <td>{clip.clip_id.slice(0, 8)}…</td>
                    <td>{clip.aspect_ratio}</td>
                    <td>{Math.round(clip.duration)}s</td>
                    <td>{upload.platform}</td>
                    <td className="status-pill success">{upload.status}</td>
                    <td>
                      <a href={upload.share_link} target="_blank" rel="noreferrer">
                        View post
                      </a>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {mutation.isError && (
        <p className="error">Unable to load task details for {taskId}.</p>
      )}
    </div>
  );
};

export default ClipStatusViewer;
