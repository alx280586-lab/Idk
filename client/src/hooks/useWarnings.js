import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';

const DEFAULT_WARNINGS = { features: [], updated: null };

export default function useWarnings() {
  const [warnings, setWarnings] = useState(DEFAULT_WARNINGS);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadWarnings = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/warnings');
      setWarnings(response.data);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadWarnings();
    const interval = window.setInterval(loadWarnings, 60 * 1000);
    return () => window.clearInterval(interval);
  }, [loadWarnings]);

  return { warnings, isLoading, error, refresh: loadWarnings };
}
