import React from 'react';
import { AlertTriangle, ShieldCheck, Heart } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-16 border-t border-slate-800/80 bg-[#040713]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-6">
        
        {/* Critical Legal & Educational Disclaimer */}
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 sm:p-5 flex items-start space-x-3.5 text-amber-200/90 text-xs sm:text-sm leading-relaxed">
          <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-amber-300 uppercase tracking-wider block mb-0.5">
              Educational & Scientific Research Disclaimer
            </span>
            <p>
              Educational and experimental ML predictions only. Lottery results are random. Predictions are not guaranteed to win.
              This platform serves solely as an academic and technological demonstration of multi-class classification, probabilistic combinatorial ranking, and cyclical feature encoding in Scikit-Learn.
            </p>
          </div>
        </div>

        {/* Branding & Status Info */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500 pt-4 border-t border-slate-900">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-slate-400">KLFINAL</span>
            <span>•</span>
            <span>Dual Machine Learning Prediction System</span>
          </div>

          <div className="flex items-center space-x-4">
            <span className="flex items-center gap-1 text-slate-400">
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
              Trained Models Verified
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              Built with <Heart className="w-3 h-3 text-rose-500 inline fill-rose-500" /> React + FastAPI
            </span>
          </div>
        </div>

      </div>
    </footer>
  );
};
