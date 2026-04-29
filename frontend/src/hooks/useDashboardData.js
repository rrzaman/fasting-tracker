import { useState, useEffect } from 'react';
import { fetchFastingData, fetchHealthData } from '../api';

export function useDashboardData() {
  const [fastingData, setFastingData] = useState({});
  const [healthData, setHealthData] = useState([]);
  const [loadingFasting, setLoadingFasting] = useState(true);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadFasting() {
      try {
        setLoadingFasting(true);
        // Fetch 90 days forward as Hijri dates rely on moon sightings
        // and predicting further ahead leads to inaccuracies.
        const fasting = await fetchFastingData(365, 90);
        const fastingMap = {};
        fasting.forEach(f => { fastingMap[f.date] = f; });
        setFastingData(fastingMap);
      } catch (err) {
        console.error('Failed to load fasting data:', err);
        setError('Failed to load fasting data.');
      } finally {
        setLoadingFasting(false);
      }
    }

    async function loadHealth() {
      try {
        setLoadingHealth(true);
        const health = await fetchHealthData(365);
        setHealthData(health);
      } catch (err) {
        console.error('Failed to load health data:', err);
        setError('Failed to load health data.');
      } finally {
        setLoadingHealth(false);
      }
    }
    
    loadFasting();
    loadHealth();
  }, []);

  return { fastingData, healthData, loadingFasting, loadingHealth, error };
}
