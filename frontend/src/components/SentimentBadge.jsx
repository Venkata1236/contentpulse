const SentimentBadge = ({ sentiment_score }) => {
  const getBadgeConfig = (score) => {
    if (score > 0.75) {
      return {
        label: "Loved",
        percentage: Math.round(score * 100),
        className: "bg-green-500 text-white",
      };
    } else if (score >= 0.5) {
      return {
        label: "Mixed",
        percentage: Math.round(score * 100),
        className: "bg-yellow-500 text-black",
      };
    } else {
      return {
        label: "Divisive",
        percentage: Math.round(score * 100),
        className: "bg-red-500 text-white",
      };
    }
  };

  const config = getBadgeConfig(sentiment_score);

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${config.className}`}
    >
      {config.label} · {config.percentage}%
    </span>
  );
};

export default SentimentBadge;