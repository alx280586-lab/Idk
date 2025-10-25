import React, { useEffect, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';

import api from '../hooks/useApi';

const AutomationPanel = () => {
  const [form, setForm] = useState({ enabled: false, daily_cap: 5 });

  const query = useQuery({
    queryKey: ['automation'],
    queryFn: async () => {
      const { data } = await api.get('/automation/');
      return data;
    },
  });

  useEffect(() => {
    if (query.data) {
      setForm(query.data);
    }
  }, [query.data]);

  const mutation = useMutation({
    mutationFn: async (payload) => {
      const { data } = await api.post('/automation/', payload);
      return data;
    },
    onSuccess: (data) => setForm(data),
  });

  const handleSubmit = (event) => {
    event.preventDefault();
    mutation.mutate(form);
  };

  return (
    <form className="form" onSubmit={handleSubmit}>
      <label className="checkbox">
        <input
          type="checkbox"
          name="enabled"
          checked={form.enabled}
          onChange={(event) => setForm((current) => ({ ...current, enabled: event.target.checked }))}
        />
        Enable fully autonomous mode
      </label>
      <label>
        Daily publishing limit
        <input
          type="number"
          min="1"
          max="20"
          value={form.daily_cap}
          onChange={(event) => setForm((current) => ({ ...current, daily_cap: Number(event.target.value) }))}
        />
      </label>
      <button type="submit" disabled={mutation.isLoading}>
        {mutation.isLoading ? 'Saving…' : 'Update automation'}
      </button>
      <p className="muted small">When enabled, AutoClipper AI will generate, edit, and schedule clips 24/7.</p>
    </form>
  );
};

export default AutomationPanel;
