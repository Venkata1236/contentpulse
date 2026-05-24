import { useRef } from "react";
import ContentCard from "./ContentCard";

const ContentRow = ({ title, films, onCardClick }) => {
  const scrollRef = useRef(null);

  const scroll = (direction) => {
    const container = scrollRef.current;
    if (!container) return;
    const amount = direction === "left" ? -400 : 400;
    container.scrollBy({ left: amount, behavior: "smooth" });
  };

  if (!films || films.length === 0) return null;

  return (
    <div className="mb-8">
      {/* ── Row Header ── */}
      <div className="flex items-center justify-between px-6 mb-3">
        <h2 className="text-white text-xl font-bold hover:text-zinc-300 cursor-pointer transition-colors">
          {title}
        </h2>
        <button className="text-sm text-zinc-400 hover:text-white transition-colors">
          See all
        </button>
      </div>

      {/* ── Scroll Container ── */}
      <div className="relative group">
        {/* Left Arrow */}
        <button
          onClick={() => scroll("left")}
          className="absolute left-0 top-0 bottom-0 z-20 w-12 bg-gradient-to-r from-black/80 to-transparent
            flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200"
        >
          <svg
            className="w-6 h-6 text-white"
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

        {/* Cards */}
        <div
          ref={scrollRef}
          className="flex gap-3 overflow-x-auto scrollbar-hide px-6 pb-4"
          style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
        >
          {films.map((film) => (
            <ContentCard
              key={film.film_id}
              {...film}
              onClick={onCardClick}
            />
          ))}
        </div>

        {/* Right Arrow */}
        <button
          onClick={() => scroll("right")}
          className="absolute right-0 top-0 bottom-0 z-20 w-12 bg-gradient-to-l from-black/80 to-transparent
            flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200"
        >
          <svg
            className="w-6 h-6 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>
      </div>
    </div>
  );
};


const ContentGrid = ({ hiddenGems, highlyRated, results, onCardClick }) => {
  // ── Filter Mode (from SearchResultsPage) ──
  if (results) {
    return (
      <div className="mt-4">
        <ContentRow
          title="Search Results"
          films={results}
          onCardClick={onCardClick}
        />
      </div>
    );
  }

  // ── Browse Mode (BrowsePage) ──
  return (
    <div className="mt-4">
      <ContentRow
        title="✨ Hidden Gems"
        films={hiddenGems}
        onCardClick={onCardClick}
      />
      <ContentRow
        title="⭐ Highly Rated"
        films={highlyRated}
        onCardClick={onCardClick}
      />
    </div>
  );
};

export default ContentGrid;