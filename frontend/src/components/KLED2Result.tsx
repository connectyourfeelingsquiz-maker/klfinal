import React, { useState } from 'react';
import { Network, Copy, Check, Binary, Compass, Zap } from 'lucide-react';

interface KLED2ResultProps {
  prediction: string;
  date: string;
  lottery: string;
}

export const KLED2Result: React.FC<KLED2ResultProps> = ({ prediction, date, lottery }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(prediction);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Split prediction into 6 individual digits preserving leading zeros
  const digits = prediction ? prediction.padStart(6, '0').split('') : [];

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-7 relative border border-slate-700/60 shadow-xl flex flex-col h-full">
      {/* Accent glow */}
      <div className="absolute top-0 right-0 -mt-10 -mr-10 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header section */}
      <div className="flex items-start justify-between pb-5 border-b border-slate-800/80 mb-6">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
            <Network className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xl font-bold text-white tracking-tight">KLED2 Cyclical Net</h3>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Single Consensus Prediction
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Multi-algorithm cyclical temporal network with sinusoidal trigonometric harmonics
            </p>
          </div>
        </div>

        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-xs font-medium text-slate-300 hover:text-white border border-slate-700 transition-colors shadow-sm"
          title="Copy KLED2 prediction"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Main Prediction Display Tile */}
      <div className="flex-1 flex flex-col justify-center my-4">
        <div className="relative p-6 sm:p-8 rounded-2xl bg-gradient-to-b from-indigo-950/40 via-slate-900/60 to-slate-950/80 border border-indigo-500/30 shadow-2xl ring-1 ring-indigo-500/20 text-center overflow-hidden">
          
          <div className="text-xs uppercase tracking-widest font-mono text-indigo-300/80 mb-4 flex items-center justify-center gap-2">
            <Zap className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
            <span>Optimal 6-Digit Composite</span>
          </div>

          {/* 6 Digit Tiles with Leading Zeros Preserved */}
          <div className="flex items-center justify-center gap-2 sm:gap-3.5 my-2">
            {digits.map((digit, index) => (
              <div
                key={index}
                className="relative group flex flex-col items-center"
              >
                <div className="w-11 sm:w-16 h-16 sm:h-20 rounded-xl bg-slate-900/90 border-2 border-indigo-500/40 group-hover:border-indigo-400 flex items-center justify-center shadow-lg shadow-indigo-950/50 transition-all duration-300 group-hover:scale-105 group-hover:-translate-y-1">
                  <span className="font-mono text-3xl sm:text-4xl font-black text-white group-hover:text-indigo-200 transition-colors">
                    {digit}
                  </span>
                </div>
                <span className="text-[10px] font-mono text-slate-500 mt-1.5 uppercase">
                  D{index + 1}
                </span>
              </div>
            ))}
          </div>

          <div className="mt-5 flex items-center justify-center gap-3">
            <span className="text-xs font-mono text-slate-400 bg-slate-900/80 px-3 py-1 rounded-md border border-slate-800">
              Target: <strong className="text-white">{lottery}</strong>
            </span>
            <span className="text-xs font-mono text-slate-400 bg-slate-900/80 px-3 py-1 rounded-md border border-slate-800">
              Draw Date: <strong className="text-white">{date}</strong>
            </span>
          </div>

        </div>

        {/* Cyclical Feature Details Grid */}
        <div className="grid grid-cols-3 gap-2.5 mt-5">
          <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 text-center">
            <div className="flex items-center justify-center gap-1 text-[11px] font-medium text-slate-400 mb-0.5">
              <Compass className="w-3 h-3 text-indigo-400" />
              <span>Month Cycle</span>
            </div>
            <p className="text-[10px] font-mono text-indigo-300">SIN / COS (12M)</p>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 text-center">
            <div className="flex items-center justify-center gap-1 text-[11px] font-medium text-slate-400 mb-0.5">
              <Compass className="w-3 h-3 text-cyan-400" />
              <span>Week Cycle</span>
            </div>
            <p className="text-[10px] font-mono text-cyan-300">SIN / COS (7D)</p>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 text-center">
            <div className="flex items-center justify-center gap-1 text-[11px] font-medium text-slate-400 mb-0.5">
              <Binary className="w-3 h-3 text-emerald-400" />
              <span>Year Cycle</span>
            </div>
            <p className="text-[10px] font-mono text-emerald-300">SIN / COS (365D)</p>
          </div>
        </div>
      </div>

      {/* Footer metadata info */}
      <div className="mt-4 pt-4 border-t border-slate-800/80 text-[11px] text-slate-500 flex items-center justify-between">
        <span>Features: 12 Cyclical & Calendar Dimensions</span>
        <span className="font-mono text-slate-400">Model: PKL Ensemble</span>
      </div>

    </div>
  );
};
