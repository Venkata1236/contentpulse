import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ─── Sentiment ────────────────────────────────────────────

export const getSentiment = async (texts) => {
  const response = await api.post("/sentiment", { texts });
  return response.data;
};

// ─── Recommendations ──────────────────────────────────────

export const getRecommendations = async (filmId, userId = "guest", n = 10) => {
  const response = await api.post("/recommend", {
    film_id: filmId,
    user_id: userId,
    n,
  });
  return response.data;
};

// ─── NL Search ────────────────────────────────────────────

export const nlSearch = async (query, userId = "guest") => {
  const response = await api.post("/search", {
    user_id: userId,
    query,
  });
  return response.data;
};

// ─── Health ───────────────────────────────────────────────

export const checkHealth = async () => {
  const response = await api.get("/health");
  return response.data;
};

export default api;