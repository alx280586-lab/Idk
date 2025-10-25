import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import api from '../hooks/useApi';

const VideoAnalytics = () => {
  const [taskId, setTaskId] = useState('');
  const [insights, setInsights] = useState(null);

  const mutation = useMutation({
    mutationFn: async (id) => {
      const { data } = await api.get(`/analytics/${id}`);
      return data;
    },
    onSuccess: (data) => setInsights(data),
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
          {mutation.isLoading ? 'Loading…' : 'Fetch insights'}
        </button>
      </form>
      {insights && (
        <div className="analytics-grid">
          <div className="card">
            <h3>Recommended Actions</h3>
            <ul>
              {insights.recommended_actions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          </div>
          <div className="card">
            <h3>Top Keywords</h3>
            <div className="chips">
              {insights.best_keywords.map((keyword) => (
                <span className="chip" key={keyword}>
                  #{keyword}
                </span>
              ))}
            </div>
          </div>
          <div className="card wide">
            <h3>Platform Performance</h3>
            <table>
              <thead>
                <tr>
                  <th>Platform</th>
                  <th>Views</th>
                  <th>Likes</th>
                  <th>Shares</th>
                  <th>Retention</th>
                </tr>
              </thead>
              <tbody>
                {insights.performances.map((item) => (
                  <tr key={`${item.clip_id}-${item.platform}`}>
                    <td>{item.platform}</td>
                    <td>{item.views.toLocaleString()}</td>
                    <td>{item.likes.toLocaleString()}</td>
                    <td>{item.shares.toLocaleString()}</td>
                    <td>{Math.round(item.retention * 100)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {mutation.isError && <p className="error">Unable to load analytics for {taskId}.</p>}
    </div>
  );
};

export default VideoAnalytics;
