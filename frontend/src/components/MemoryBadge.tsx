import React from 'react';
import { Brain } from 'lucide-react';

interface Props { memoryState: string; }

export function MemoryBadge({ memoryState }: Props) {
  if (memoryState === 'historical') {
    return (
      <div className="flex items-center gap-1.5 bg-blue-950 border border-blue-800 px-3 py-1.5 rounded-full">
        <Brain className="w-3.5 h-3.5 text-blue-400" />
        <span className="text-xs text-blue-300 font-medium">Historical Memory Active</span>
      </div>
    );
  }
  if (memoryState === 'learned') {
    return (
      <div className="flex items-center gap-1.5 bg-green-950 border border-green-800 px-3 py-1.5 rounded-full">
        <Brain className="w-3.5 h-3.5 text-green-400" />
        <span className="text-xs text-green-300 font-medium">Memory Learned</span>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-1.5 bg-gray-800 border border-gray-700 px-3 py-1.5 rounded-full">
      <Brain className="w-3.5 h-3.5 text-gray-500" />
      <span className="text-xs text-gray-400 font-medium">No Memory</span>
    </div>
  );
}
