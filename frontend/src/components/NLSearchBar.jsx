import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { nlSearch } from "../services/api";

const EXAMPLE_QUERIES = [
  "inspiring biopics under 2 hours",
  "feel-good comedies from the 90s",
  "dark psychological thrillers",
  "romantic movies with happy endings",
  "action movies with strong female leads",
];

const NLSearchBar = () => {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSearch = async (searchQuery) => {
    const q = searchQuery || query;
    if (!q.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const results = await nlSearch(q.trim());
      navigate("/search", {
        state: { results, query: q.trim() },
      });
    } catch (err) {
      setError("Search failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSearch();
  };

  return (
    <div className="w-full max-w-3xl mx-auto px-4">
      {/* ── Search Input ── */}
      <div className="relative flex items-center">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Try: inspiring biopics under 2 hours with positive reviews..."
          disabled={loading}
          className="w-full bg-zinc-800 border border-zinc-600 focus:border-red-500 text-white placeholder-zinc-500
            rounded-full px-6 py-3.5 pr-36 text-sm outline-none transition-all duration-200"
        />
        <button
          onClick={() => handleSearch()}
          disabled={loading || !query.trim()}
          className={`absolute right-2 px-5 py-2 rounded-full text-sm font-semibold transition-all duration-200
            ${
              loading || !query.trim()
                ? "bg-zinc-700 text-zinc-500 cursor-not-allowed"
                : "bg-red-600 hover:bg-red-500 text-white cursor-pointer"
            }`}
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg
                className="animate-spin h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v8z"
                />
              </svg>
              Searching...
            </span>
          ) : (
            "Search"
          )}
        </button>
      </div>

      {/* ── Error ── */}
      {error && (
        <p className="text-red-400 text-xs mt-2 text-center">{error}</p>
      )}

      {/* ── Example Queries ── */}
      <div className="flex flex-wrap gap-2 mt-3 justify-center">
        {EXAMPLE_QUERIES.map((q) => (
          <button
            key={q}
            onClick={() => {
              setQuery(q);
              handleSearch(q);
            }}
            className="text-xs text-zinc-400 hover:text-white border border-zinc-700 hover:border-zinc-500
              px-3 py-1 rounded-full transition-all duration-200"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
};

export default NLSearchBar;