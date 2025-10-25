import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import api from '../hooks/useApi';

const defaultForm = {
  youtube_url: '',
  clip_duration_min: 15,
  clip_duration_max: 60,
  auto_subtitles: true,
  include_emojis: false,
  include_captions: true,
  aspect_ratios: ['9:16'],
  target_platforms: ['tiktok', 'youtube_shorts', 'instagram_reels'],
};

const UploadForm = () => {
  const [form, setForm] = useState(defaultForm);

  const mutation = useMutation({
    mutationFn: async (payload) => {
      const { data } = await api.post('/videos/ingest', payload);
      return data;
    },
  });

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    if (type === 'checkbox') {
      setForm((current) => ({ ...current, [name]: checked }));
    } else {
      setForm((current) => ({ ...current, [name]: value }));
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    mutation.mutate({
      ...form,
      clip_duration_min: Number(form.clip_duration_min),
      clip_duration_max: Number(form.clip_duration_max),
    });
  };

  return (
    <form className="form" onSubmit={handleSubmit}>
      <label>
        YouTube Link
        <input
          type="url"
          name="youtube_url"
          placeholder="https://youtube.com/watch?v=..."
          required
          value={form.youtube_url}
          onChange={handleChange}
        />
      </label>
      <div className="form-row">
        <label>
          Min Duration (sec)
          <input
            type="number"
            name="clip_duration_min"
            min="5"
            max="120"
            value={form.clip_duration_min}
            onChange={handleChange}
          />
        </label>
        <label>
          Max Duration (sec)
          <input
            type="number"
            name="clip_duration_max"
            min="15"
            max="180"
            value={form.clip_duration_max}
            onChange={handleChange}
          />
        </label>
      </div>
      <label className="checkbox">
        <input
          type="checkbox"
          name="auto_subtitles"
          checked={form.auto_subtitles}
          onChange={handleChange}
        />
        Auto subtitles
      </label>
      <label className="checkbox">
        <input
          type="checkbox"
          name="include_emojis"
          checked={form.include_emojis}
          onChange={handleChange}
        />
        Add emoji reactions
      </label>
      <label className="checkbox">
        <input
          type="checkbox"
          name="include_captions"
          checked={form.include_captions}
          onChange={handleChange}
        />
        Add captions overlay
      </label>
      <label>
        Aspect Ratios (comma separated)
        <input
          type="text"
          name="aspect_ratios"
          value={form.aspect_ratios.join(', ')}
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              aspect_ratios: event.target.value
                .split(',')
                .map((item) => item.trim())
                .filter(Boolean),
            }))
          }
        />
      </label>
      <label>
        Target Platforms (comma separated)
        <input
          type="text"
          name="target_platforms"
          value={form.target_platforms.join(', ')}
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              target_platforms: event.target.value
                .split(',')
                .map((item) => item.trim())
                .filter(Boolean),
            }))
          }
        />
      </label>
      <button type="submit" disabled={mutation.isLoading}>
        {mutation.isLoading ? 'Processing…' : 'Generate Clips'}
      </button>
      {mutation.data && (
        <p className="success">Task queued! Reference ID: {mutation.data.task_id}</p>
      )}
      {mutation.error && <p className="error">{mutation.error.message}</p>}
    </form>
  );
};

export default UploadForm;
