import { useEffect, useState } from 'react';
import axios from 'axios';

const PRODUCT_KEYS = ['reflectivity', 'velocity', 'correlationCoefficient', 'echoTops'];

export default function useRadarProducts() {
  const [timelines, setTimelines] = useState({});
  const [legends, setLegends] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setIsLoading(true);
      setError(null);
      try {
        const [productsResponse] = await Promise.all([
          axios.get('/api/radar/products')
        ]);
        const availableProducts = productsResponse.data.products ?? {};

        const timelinePromises = PRODUCT_KEYS.map(async (key) => {
          if (!availableProducts[key]) return null;
          const [timelineResponse, legendResponse] = await Promise.all([
            axios.get(`/api/radar/${key}/frames`),
            axios.get(`/api/radar/${key}/legend`)
          ]);
          return { key, timeline: timelineResponse.data, legend: legendResponse.data };
        });

        const results = await Promise.all(timelinePromises);
        if (!isMounted) return;

        const nextTimelines = {};
        const nextLegends = {};
        results.filter(Boolean).forEach(({ key, timeline, legend }) => {
          nextTimelines[key] = timeline;
          nextLegends[key] = legend;
        });
        setTimelines(nextTimelines);
        setLegends(nextLegends);
      } catch (err) {
        if (!isMounted) return;
        setError(err);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadData();

    const interval = window.setInterval(loadData, 5 * 60 * 1000);
    return () => {
      isMounted = false;
      window.clearInterval(interval);
    };
  }, []);

  return { timelines, legends, isLoading, error };
}
