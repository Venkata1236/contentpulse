import { useState } from "react";

const MOODS = [
  { id: "feel-good", label: "Feel-Good", emoji: "😄" },
  { id: "drama", label: "Drama", emoji: "🎭" },
  { id: "comedy", label: "Comedy", emoji: "😂" },
  { id: "action", label: "Action", emoji: "🔥" },
  { id: "thought-provoking", label: "Thought-Provoking", emoji: "💭" },
  { id: "emotional", label: "Emotional", emoji: "😢" },
  { id: "foreign", label: "Foreign", emoji: "🌍" },
  { id: "hidden-gems", label: "Hidden Gems", emoji: "⭐" },
];

const MoodFilter = ({ onFilterChange }) => {
  const [selected, setSelected] = useState([]);

  const toggleMood = (moodId) => {
    const updated = selected.includes(moodId)
      ? selected.filter((id) => id !== moodId)
      : [...selected, moodId];

    setSelected(updated);
    onFilterChange && onFilterChange(updated);
  };

  const clearAll = () => {
    setSelected([]);
    onFilterChange && onFilterChange([]);
  };

  return (
    <div className="flex items-center gap-2 px-6 py-3 overflow-x-auto scrollbar-hide">
      {/* Clear button */}
      {selected.length > 0 && (
        <button
          onClick={clearAll}
          className="flex-shrink-0 text-xs text-zinc-400 hover:text-white border border-zinc-600 hover:border-white px-3 py-1.5 rounded-full transition-all duration-200"
        >
          Clear
        </button>
      )}

      {/* Mood chips */}
      {MOODS.map((mood) => {
        const isSelected = selected.includes(mood.id);
        return (
          <button
            key={mood.id}
            onClick={() => toggleMood(mood.id)}
            className={`flex-shrink-0 flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200 border
              ${
                isSelected
                  ? "bg-white text-black border-white"
                  : "bg-transparent text-zinc-300 border-zinc-600 hover:border-zinc-400 hover:text-white"
              }`}
          >
            <span>{mood.emoji}</span>
            <span>{mood.label}</span>
          </button>
        );
      })}
    </div>
  );
};

export default MoodFilter;