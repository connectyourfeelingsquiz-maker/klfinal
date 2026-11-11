import React, { useState } from 'react';
import { Layers, Copy, Check, TrendingUp, Award, Sparkles } from 'lucide-react';

export interface KL1Candidate {
  rank: number;
  candidate: string;
  score: number;
}

interface KL1ResultsProps {
  candidates: KL1Candidate[];
  date: string;
  lottery: string;
}

export const KL1Results: React.FC<KL1ResultsProps> = ({ candidates, date, lottery }) => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);

  const handleCopy = (candidate: string, index: number) => {
    navigator.clipboard.writeText(candidate);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleCopyAll = () => {
    const text = candidates.map(c => `#${c.rank}: ${c.candidate} (Score: ${c.score.toFixed(8)})`).join('\n');
    navigator.clipboard.writeText(`KLFINAL - KL1 Candidates for ${lottery} (${date}):\n` + text);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2000);
  };

  // Find max score for relative score bar
  const maxScore = candidates.length > 0 ? Math.max(...candidates.map(c => c.score)) : 1;

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-7 relative border border-slate-700/60 shadow-xl flex flex-col h-full">
      
      {/* Header section */}
      <div className="flex items-start justify-between pb-5 border-b border-slate-800/80 mb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-bold text-white tracking-tight">KL1 Ensemble</h3>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  Top 5 Candidates
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Combinatorial probability optimization across 6 digit estimators (729 combinations)
              </p>
            </div>
          </div>
        </div>

        {candidates.length > 0 && (
          <button
            onClick={handleCopyAll}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-xs font-medium text-slate-300 hover:text-white border border-slate-700 transition-colors shadow-sm"
            title="Copy all candidates to clipboard"
          >
            {copiedAll ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400">Copied All</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy All</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Candidate cards list */}
      <div className="space-y-3.5 flex-1">
        {candidates.map((item, index) => {
          const isTopRank = item.rank === 1;
          const percentageOfMax = Math.round((item.score / maxScore) * 100);

          return (
            <div
              key={item.candidate + index}
              className={`p-4 rounded-xl border transition-all duration-200 relative overflow-hidden group ${
                isTopRank
                  ? 'bg-gradient-to-r from-cyan-950/40 via-blue-950/30 to-slate-900/40 border-cyan-500/40 shadow-lg shadow-cyan-950/30 ring-1 ring-cyan-500/20'
                  : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-800/50'
              }`}
            >
              {/* Highlight bar on left edge */}
              <div
                className={`absolute left-0 top-0 bottom-0 w-1 ${
                  isTopRank ? 'bg-gradient-to-b from-cyan-400 to-blue-500' : 'bg-slate-700 group-hover:bg-cyan-500/50'
                }`}
              />

              <div className="flex items-center justify-between pl-2">
                
                {/* Rank & Candidate */}
                <div className="flex items-center space-x-3.5">
                  <div
                    className={`flex items-center justify-center w-8 h-8 rounded-lg font-mono font-bold text-xs ${
                      isTopRank
                        ? 'bg-gradient-to-tr from-cyan-500 to-blue-500 text-white shadow-md shadow-cyan-500/30'
                        : 'bg-slate-800 text-slate-300 border border-slate-700'
                    }`}
                  >
                    {isTopRank ? <Award className="w-4 h-4" /> : `#${item.rank}`}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-2xl font-black tracking-widest text-white group-hover:text-cyan-200 transition-colors">
                        {item.candidate}
                      </span>
                      {isTopRank && (
                        <span className="text-[10px] font-bold text-cyan-400 bg-cyan-950/80 border border-cyan-800 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <Sparkles className="w-2.5 h-2.5" />
                          Highest Probability
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-3 mt-1">
                      <div className="flex items-center gap-1 text-[11px] font-mono text-slate-400">
                        <TrendingUp className="w-3 h-3 text-cyan-400" />
                        <span>Score:</span>
                        <span className="text-cyan-300 font-semibold">{item.score.toFixed(8)}</span>
                      </div>
                      <span className="text-slate-600 text-[10px]">•</span>
                      <span className="text-[11px] font-mono text-slate-500">
                        Relative: {percentageOfMax}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Copy candidate button */}
                <button
                  onClick={() => handleCopy(item.candidate, index)}
                  className="p-2.5 rounded-lg bg-slate-800/80 hover:bg-cyan-500/20 hover:text-cyan-300 text-slate-400 border border-slate-700/80 transition-all hover:scale-105 active:scale-95 shadow-sm"
                  title={`Copy ${item.candidate}`}
                >
                  {copiedIndex === index ? (
                    <Check className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
              </div>

              {/* Relative score confidence bar */}
              <div className="mt-3 pl-2">
                <div className="w-full bg-slate-800/80 rounded-full h-1 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      isTopRank ? 'bg-gradient-to-r from-cyan-400 to-blue-500' : 'bg-slate-600 group-hover:bg-cyan-500/60'
                    }`}
                    style={{ width: `${percentageOfMax}%` }}
                  />
                </div>
              </div>

            </div>
          );
        })}
      </div>

      {/* Footer metadata info */}
      <div className="mt-6 pt-4 border-t border-slate-800/80 text-[11px] text-slate-500 flex items-center justify-between">
        <span>Features: Year, Month, Day, Weekday, DayOfYear, Lottery</span>
        <span className="font-mono text-slate-400">Model: Joblib Ensemble</span>
      </div>

    </div>
  );
};
