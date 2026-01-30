import { HistoryItem } from '../types';

const HISTORY_KEY = 'sme_assessment_history';

export const getHistory = (): HistoryItem[] => {
  try {
    const stored = localStorage.getItem(HISTORY_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (e) {
    console.error('Failed to parse history', e);
    return [];
  }
};

export const addToHistory = (item: HistoryItem): void => {
  const current = getHistory();
  // Remove duplicate if exists to move it to top
  const filtered = current.filter((h) => h.id !== item.id);
  const updated = [item, ...filtered];
  localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
};

export const clearHistory = (): void => {
  localStorage.removeItem(HISTORY_KEY);
};
