import React from 'react';

interface ConfidenceBarProps {
  confidence: number | null | undefined;
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({ confidence }) => {
  if (confidence === null || confidence === undefined) {
    return <span className="text-gray-400 text-sm">N/A</span>;
  }

  const percentage = Math.round(confidence * 100);
  let colorClass = 'bg-red-500';
  if (confidence >= 0.8) colorClass = 'bg-green-500';
  else if (confidence >= 0.5) colorClass = 'bg-yellow-500';

  return (
    <div className="flex items-center space-x-2">
      <div className="w-24 bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${colorClass}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-sm text-gray-600">{percentage}%</span>
    </div>
  );
};
