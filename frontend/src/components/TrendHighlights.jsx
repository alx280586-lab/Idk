import React from 'react';
import { useQuery } from '@tanstack/react-query';

import api from '../hooks/useApi';

const TrendHighlights = () => {
  const query = useQuery({
    queryKey: ['trends'],
    queryFn: async () => {
      const { data } = await api.get('/trends/');
      return data.trends;
    },
  });

  if (query.isLoading) {
    return <p>Scanning trends…</p>;
  }

  return (
    <ul className="trend-list">
      {query.data.map((trend) => (
        <li key={`${trend.platform}-${trend.hashtag}`}>
          <div>
            <strong>{trend.hashtag}</strong>
            <span className="muted"> · {trend.platform}</span>
          </div>
          <div className="muted">Relevance score {(trend.score * 100).toFixed(0)}%</div>
          <div className="muted">Topic: {trend.category}</div>
        </li>
      ))}
    </ul>
  );
};

export default TrendHighlights;
