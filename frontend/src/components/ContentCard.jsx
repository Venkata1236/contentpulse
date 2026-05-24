import { useState } from "react";
import SentimentBadge from "./SentimentBadge";

const ContentCard = ({
  film_id,
  title,
  genres,
  overview,
  release_year,
  duration_mins,
  sentiment_score,
  is_hidden_gem,
  why_recommended,
  poster_url,
  onClick,
}) => {
  const [hovered, setHovered] = useState(false);

  const truncateTitle = (text, max = 30) => {
    return text?.length > max ? text.slice(0, max) + "..." : text;
  };

  const formatDuration = (mins) => {
    if (!mins) return null;
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  // Gradient poster placeholder based on film_id
  const gradients = [
    "from-red-900 to-red-600",
    "from-blue-900 to-blue-600",
    "from-purple-900 to-purple-600",
    "from-green-900 to-green-600",
    "from-yellow-900 to-yellow-600",
    "from-pink-900 to-pink-600",
    "from-indigo-900 to-indigo-600",
    "from-orange-900 to-orange-600",
  ];
  const gradient = gradients[parseInt(film_id || "0") % gradients.length];

  return (
    <div
      className={`relative flex-shrink-0 w-40 md:w-44 lg:w-48 cursor-pointer transition-all duration-300 rounded-md overflow-hidden
        ${hovered ? "scale-110 z-20 shadow-2xl shadow-black" : "scale-100 z-10"}`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => onClick && onClick(film_id)}
    >
      {/* ── Poster ── */}
      <div className={`relative w-full h-60 bg-gradient-to-b ${gradient}`}>
        {poster_url ? (
          <img
            src={poster_url}
            alt={title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center p-3">
            <span className="text-white text-sm font-bold text-center leading-tight">
              {title}
            </span>
          </div>
        )}

        {/* Hidden Gem Badge */}
        {is_hidden_gem && (
          <div className="absolute top-2 left-2 bg-yellow-400 text-black text-xs font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
            ✨ Hidden Gem
          </div>
        )}
      </div>

      {/* ── Info ── */}
      <div className="bg-zinc-900 p-2">
        <p className="text-white text-sm font-semibold truncate">
          {truncateTitle(title)}
        </p>

        {/* Genre tags — max 2 */}
        <div className="flex gap-1 mt-1 flex-wrap">
          {genres?.slice(0, 2).map((genre) => (
            <span
              key={genre}
              className="text-xs text-zinc-400 bg-zinc-800 px-1.5 py-0.5 rounded"
            >
              {genre}
            </span>
          ))}
        </div>

        {/* Sentiment Badge */}
        <div className="mt-1.5">
          <SentimentBadge sentiment_score={sentiment_score} />
        </div>

        {/* Meta info */}
        <div className="flex gap-2 mt-1 text-xs text-zinc-500">
          {release_year && <span>{release_year}</span>}
          {duration_mins && <span>{formatDuration(duration_mins)}</span>}
        </div>
      </div>

      {/* ── Hover Tooltip ── */}
      {hovered && why_recommended && (
        <div className="absolute bottom-full left-0 right-0 mb-2 bg-zinc-800 border border-zinc-700 rounded-md p-3 text-xs text-zinc-200 shadow-xl z-30">
          <p className="font-semibold text-white mb-1">Why you'll love it:</p>
          <p>{why_recommended}</p>
          {genres && genres.length > 2 && (
            <div className="flex gap-1 mt-2 flex-wrap">
              {genres.map((genre) => (
                <span
                  key={genre}
                  className="text-xs text-zinc-400 bg-zinc-700 px-1.5 py-0.5 rounded"
                >
                  {genre}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ContentCard;