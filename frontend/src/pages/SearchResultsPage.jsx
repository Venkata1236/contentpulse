import { useLocation, useNavigate } from "react-router-dom";
import ContentGrid from "../components/ContentGrid";
import NLSearchBar from "../components/NLSearchBar";

const FilterChip = ({ label, value }) => {
  if (!value) return null;
  const display = Array.isArray(value) ? value.join(", ") : value;
  return (
    <span className="inline-flex items-center gap-1 bg-zinc-800 border border-zinc-700 text-zinc-300 text-xs px-3 py-1 rounded-full">
      <span className="text-zinc-500">{label}:</span>
      <span className="text-white font-medium">{display}</span>
    </span>
  );
};

const SearchResultsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const { results, query } = location.state || {};

  // No results state — user navigated directly
  if (!results) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="text-center">
          <p className="text-zinc-400 text-lg mb-4">No search results found.</p>
          <button
            onClick={() => navigate("/")}
            className="bg-red-600 hover:bg-red-500 text-white px-6 py-2 rounded-full text-sm font-semibold"
          >
            Back to Browse
          </button>
        </div>
      </div>
    );
  }

  const { extracted_filters, total_found } = results;
  const films = results.results || [];

  return (
    <div className="min-h-screen bg-zinc-950">
      {/* ── Header ── */}
      <div className="bg-gradient-to-b from-zinc-900 to-zinc-950 pt-8 pb-6">
        {/* Logo + Back */}
        <div className="px-6 mb-6 flex items-center gap-4">
          <button
            onClick={() => navigate("/")}
            className="text-zinc-400 hover:text-white transition-colors"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </button>
          <h1 className="text-red-600 text-2xl font-black tracking-tight">
            CONTENT<span className="text-white">PULSE</span>
          </h1>
        </div>

        {/* Search Bar */}
        <NLSearchBar />
      </div>

      {/* ── Query + Filters ── */}
      <div className="px-6 py-4 border-b border-zinc-800">
        <p className="text-zinc-400 text-sm mb-3">
          Results for{" "}
          <span className="text-white font-semibold">"{query}"</span>
          {" "}·{" "}
          <span className="text-red-400">{total_found} films found</span>
        </p>

        {/* Extracted Filters Chips */}
        {extracted_filters && (
          <div className="flex flex-wrap gap-2">
            <FilterChip
              label="Genre"
              value={extracted_filters.genres}
            />
            <FilterChip
              label="Mood"
              value={extracted_filters.mood}
            />
            <FilterChip
              label="Max Duration"
              value={
                extracted_filters.max_duration_mins
                  ? `${extracted_filters.max_duration_mins} min`
                  : null
              }
            />
            <FilterChip
              label="Min Sentiment"
              value={
                extracted_filters.min_sentiment
                  ? `${Math.round(extracted_filters.min_sentiment * 100)}%`
                  : null
              }
            />
            <FilterChip
              label="Decade"
              value={extracted_filters.decade}
            />
          </div>
        )}
      </div>

      {/* ── Results Grid ── */}
      <div className="pt-4">
        {films.length > 0 ? (
          <ContentGrid
            results={films}
            onCardClick={(filmId) => console.log("Clicked:", filmId)}
          />
        ) : (
          <div className="flex flex-col items-center justify-center h-64 gap-4">
            <p className="text-zinc-400 text-lg">
              No results found for "{query}"
            </p>
            <p className="text-zinc-500 text-sm">
              Try: "action movies from 2010s" or "romantic comedies"
            </p>
            <button
              onClick={() => navigate("/")}
              className="bg-red-600 hover:bg-red-500 text-white px-6 py-2 rounded-full text-sm font-semibold mt-2"
            >
              Back to Browse
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchResultsPage;