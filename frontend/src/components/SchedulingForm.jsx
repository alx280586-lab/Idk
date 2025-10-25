import React, { useEffect, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';

import api from '../hooks/useApi';

const SchedulingForm = () => {
  const [form, setForm] = useState({ posts_per_day: 3, auto_optimize: true, preferred_slots: [] });

  const query = useQuery({
    queryKey: ['schedule'],
    queryFn: async () => {
      const { data } = await api.get('/schedule/');
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
      const { data } = await api.put('/schedule/', payload);
      return data;
    },
    onSuccess: (data) => setForm(data),
  });

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    if (type === 'checkbox') {
      setForm((current) => ({ ...current, [name]: checked }));
    } else {
      setForm((current) => ({ ...current, [name]: Number(value) }));
    }
  };

  if (query.isLoading) {
    return <p>Loading schedule…</p>;
  }

  return (
    <form className="form" onSubmit={(event) => { event.preventDefault(); mutation.mutate(form); }}>
      <label>
        Posts per day
        <input
          type="number"
          name="posts_per_day"
          min="1"
          max="20"
          value={form.posts_per_day}
          onChange={handleChange}
        />
      </label>
      <label className="checkbox">
        <input
          type="checkbox"
          name="auto_optimize"
          checked={form.auto_optimize}
          onChange={handleChange}
        />
        Auto optimize times
      </label>
      <button type="submit" disabled={mutation.isLoading}>
        {mutation.isLoading ? 'Updating…' : 'Save preferences'}
      </button>
    </form>
  );
};

export default SchedulingForm;
