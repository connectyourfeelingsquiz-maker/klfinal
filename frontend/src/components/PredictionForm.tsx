import React from 'react';
import { Calendar, Ticket, Wand2, Loader2, RefreshCw } from 'lucide-react';

interface PredictionFormProps {
  date: string;
  setDate: (date: string) => void;
  lottery: string;
  setLottery: (lottery: string) => void;
  lotteries: string[];
  isLoadingLotteries: boolean;
  onRefreshLotteries: () => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  backendStatus: 'online' | 'checking' | 'offline';
}

export const PredictionForm: React.FC<PredictionFormProps> = ({
  date,
  setDate,
  lottery,
  setLottery,
  lotteries,
  isLoadingLotteries,
  onRefreshLotteries,
  onSubmit,
  isLoading,
  backendStatus,
}) => {
  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-8 relative overflow-hidden border border-slate-700/60 shadow-2xl">
      {/* Glow accent highlight */}
      <div className="absolute top-0 right-0 -mt-12 -mr-12 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 -mb-12 -ml-12 w-64 h-64 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="mb-6">
        <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <Wand2 className="w-5 h-5 text-cyan-400" />
          <span>Unified Draw Input</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Select draw parameters. Both <strong className="text-cyan-400 font-semibold">KL1</strong> (Combinatorial Probability) and <strong className="text-indigo-400 font-semibold">KLED2</strong> (Cyclical Feature Net) models evaluate the exact same input simultaneously.
        </p>
      </div>

      <form onSubmit={onSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          
          {/* Date Picker Input */}
          <div className="space-y-2">
            <label htmlFor="draw-date" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-cyan-400" />
                Draw Date
              </span>
              <span className="text-[11px] font-mono text-slate-500">YYYY-MM-DD</span>
            </label>
            <div className="relative rounded-xl shadow-sm">
              <input
                id="draw-date"
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
                className="w-full glass-input px-4 py-3 rounded-xl text-sm font-mono text-white focus:ring-2 focus:ring-cyan-400/50 focus:border-cyan-400 transition-all cursor-pointer"
              />
            </div>
            <p className="text-[11px] text-slate-500">
              Target date for calculating calendar and cyclical trigonometric features.
            </p>
          </div>

          {/* Lottery Dropdown */}
          <div className="space-y-2">
            <label htmlFor="lottery-name" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Ticket className="w-3.5 h-3.5 text-indigo-400" />
                Kerala Lottery Name
              </span>
              <button
                type="button"
                onClick={onRefreshLotteries}
                disabled={isLoadingLotteries}
                title="Reload lotteries from backend"
                className="text-[11px] text-slate-400 hover:text-cyan-400 flex items-center gap-1 transition-colors"
              >
                <RefreshCw className={`w-3 h-3 ${isLoadingLotteries ? 'animate-spin text-cyan-400' : ''}`} />
                <span>Sync</span>
              </button>
            </label>
            <div className="relative rounded-xl shadow-sm">
              <select
                id="lottery-name"
                value={lottery}
                onChange={(e) => setLottery(e.target.value)}
                required
                disabled={isLoadingLotteries && lotteries.length === 0}
                className="w-full glass-input px-4 py-3 rounded-xl text-sm font-medium text-white focus:ring-2 focus:ring-indigo-400/50 focus:border-indigo-400 transition-all cursor-pointer appearance-none bg-[#090f23]"
              >
                {lotteries.map((item) => (
                  <option key={item} value={item} className="bg-slate-900 text-white py-2">
                    {item}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400">
                <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
                  <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                </svg>
              </div>
            </div>
            <p className="text-[11px] text-slate-500">
              Matches one-hot encoded categories across all digit estimators.
            </p>
          </div>

        </div>

        {/* Submit Button */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={isLoading || backendStatus === 'offline'}
            className="w-full relative group overflow-hidden rounded-xl p-[1px] focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 rounded-xl group-hover:from-cyan-400 group-hover:via-blue-500 group-hover:to-indigo-500 transition-all duration-300" />
            <div className="relative px-6 py-4 rounded-[11px] bg-[#070e24]/90 group-hover:bg-[#070e24]/75 transition-colors flex items-center justify-center space-x-3">
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
                  <span className="font-semibold text-white tracking-wide">
                    Running Dual ML Inference Pipelines...
                  </span>
                </>
              ) : (
                <>
                  <Wand2 className="w-5 h-5 text-cyan-400 group-hover:rotate-12 transition-transform duration-300" />
                  <span className="font-bold text-white text-base tracking-wide">
                    Predict Results (KL1 & KLED2)
                  </span>
                </>
              )}
            </div>
          </button>
        </div>
      </form>
    </div>
  );
};
