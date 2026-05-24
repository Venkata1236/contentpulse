import { useState, useEffect } from "react";
import { getRecommendations } from "../services/api";
import ContentGrid from "../components/ContentGrid";
import MoodFilter from "../components/MoodFilter";
import NLSearchBar from "../components/NLSearchBar";

// Featured film IDs from TMDB dataset
const FEATURED_FILM_IDS = [
  "19995", // Avatar
  "299536", // Avengers Infinity War
  "140607", // Star Wars Force Awakens
  "158852", // Tomorrowland
  "102382", // Amazing Spider-Man 2
];

const BrowsePage = () => {
  const [allFilms, setAllFilms] = useState([]);
  const [filteredFilms, setFilteredFilms] = useState([]);
  const [hiddenGems, setHiddenGems] = useState([]);
  const [highlyRated, setHighlyRated] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedMoods, setSelectedMoods] = useState([]);

  useEffect(() => {
    loadContent();
  }, []);

  const loadContent = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load recommendations for multiple seed films
      const promises = FEATURED_FILM_IDS.map((id) =>
        getRecommendations(id, "guest", 10)
      );
      const results = await Promise.all(promises);

      // Flatten and deduplicate
      const seen = new Set();
      const combined = [];
      results.forEach((result) => {
        result.recommendations?.forEach((film) => {
          if (!seen.has(film.film_id)) {
            seen.add(film.film_id);
            combined.push(film);
          }
        });
      });

      setAllFilms(combined);
      setFilteredFilms(combined);

      // Split into rows
      const gems = combined.filter((f) => f.is_hidden_gem);
      const rated = combined
        .filter((f) => f.sentiment_score >= 0.6)
        .sort((a, b) => b.sentiment_score - a.sentiment_score)
        .slice(0, 20);

      // Fallback — if no hidden gems yet (before fine-tuning)
      setHiddenGems(
        gems.length > 0 ? gems : combined.slice(0, 10)
      );
      setHighlyRated(
        rated.length > 0 ? rated : combined.slice(10, 30)
      );
    } catch (err) {
      setError("Failed to load content. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const handleMoodFilter = (moods) => {
    setSelectedMoods(moods);

    if (moods.length === 0) {
      setHiddenGems(allFilms.filter((f) => f.is_hidden_gem).slice(0, 20));
      setHighlyRated(
        allFilms
          .filter((f) => f.sentiment_score >= 0.6)
          .slice(0, 20)
      );
      return;
    }

    const moodToGenre = {
      "feel-good": ["Comedy", "Romance", "Animation", "Family"],
      drama: ["Drama"],
      comedy: ["Comedy"],
      action: ["Action", "Adventure", "Thriller"],
      "thought-provoking": ["Documentary", "Drama", "Science Fiction"],
      emotional: ["Drama", "Romance"],
      foreign: [],
      "hidden-gems": [],
    };

    const filtered = allFilms.filter((film) => {
      return moods.some((mood) => {
        if (mood === "hidden-gems") return film.is_hidden_gem;
        const targetGenres = moodToGenre[mood] || [];
        return film.genres?.some((g) => targetGenres.includes(g));
      });
    });

    setHiddenGems(filtered.filter((f) => f.is_hidden_gem).slice(0, 20));
    setHighlyRated(filtered.slice(0, 20));
  };

  const handleCardClick = (filmId) => {
    // Future: navigate to film detail page
    console.log("Film clicked:", filmId);
  };

  return (
    <div className="min-h-screen bg-zinc-950">
      {/* ── Hero Header ── */}
      <div className="bg-gradient-to-b from-zinc-900 to-zinc-950 pt-8 pb-6">
        {/* Logo */}
        <div className="px-6 mb-6">
          <h1 className="text-red-600 text-3xl font-black tracking-tight">
            CONTENT<span className="text-white">PULSE</span>
          </h1>
          <p className="text-zinc-400 text-sm mt-1">
            Sentiment-powered recommendations · Hidden gems surfaced
          </p>
        </div>

        {/* NL Search Bar */}
        <NLSearchBar />
      </div>

      {/* ── Mood Filter ── */}
      <div className="bg-zinc-900 border-b border-zinc-800 sticky top-0 z-10">
        <MoodFilter onFilterChange={handleMoodFilter} />
      </div>

      {/* ── Content ── */}
      <div className="pt-6">
        {loading && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-red-600 mx-auto mb-4" />
              <p className="text-zinc-400 text-sm">Loading content...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <p className="text-red-400 text-lg mb-2">⚠️ {error}</p>
              <button
                onClick={loadContent}
                className="text-sm text-zinc-400 hover:text-white border border-zinc-600 px-4 py-2 rounded-full"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {!loading && !error && (
          <ContentGrid
            hiddenGems={hiddenGems}
            highlyRated={highlyRated}
            onCardClick={handleCardClick}
          />
        )}
      </div>
    </div>
  );
};

export default BrowsePage;