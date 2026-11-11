import React from 'react';
import { Cpu, Activity, Sparkles, ShieldCheck } from 'lucide-react';

interface HeaderProps {
  backendStatus: 'online' | 'checking' | 'offline';
  modelsLoaded: boolean;
}

export const Header: React.FC<HeaderProps> = ({ backendStatus, modelsLoaded }) => {
  return (
    <header className="border-b border-slate-800/80 bg-[#060b1b]/80 backdrop-blur-xl sticky top-0 z-50 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        
        {/* Brand identity */}
        <div className="flex items-center space-x-3.5">
          <div className="relative flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-600 shadow-lg shadow-cyan-500/20 ring-1 ring-white/20">
            <Cpu className="w-6 h-6 text-white animate-pulse" />
            <div className="absolute -inset-0.5 rounded-xl bg-cyan-400/20 blur-sm -z-10" />
          </div>

          <div>
            <div className="flex items-center space-x-2">
              <span className="text-2xl font-black tracking-wider bg-gradient-to-r from-white via-sky-100 to-cyan-400 bg-clip-text text-transparent">
                KLFINAL
              </span>
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                PROD v1.0
              </span>
            </div>
            <p className="text-xs font-medium text-slate-400 tracking-tight flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-cyan-400 inline" />
              Dual Machine Learning Prediction System
            </p>
          </div>
        </div>

        {/* Backend status indicator */}
        <div className="flex items-center space-x-3">
          <div className="hidden sm:flex items-center space-x-2 text-xs font-mono bg-slate-900/80 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-300">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Dual Models:</span>
            <span className="text-cyan-400 font-bold">KL1</span>
            <span className="text-slate-600">+</span>
            <span className="text-indigo-400 font-bold">KLED2</span>
          </div>

          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full border text-xs font-medium transition-all shadow-sm">
            {backendStatus === 'online' && (
              <span className="inline-flex items-center gap-2 text-emerald-400 border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 rounded-full border">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span>Backend Online {modelsLoaded ? '(Models Ready)' : ''}</span>
              </span>
            )}

            {backendStatus === 'checking' && (
              <span className="inline-flex items-center gap-2 text-amber-400 border-amber-500/30 bg-amber-500/10 px-2.5 py-1 rounded-full border">
                <Activity className="w-3.5 h-3.5 animate-spin" />
                <span>Connecting...</span>
              </span>
            )}

            {backendStatus === 'offline' && (
              <span className="inline-flex items-center gap-2 text-rose-400 border-rose-500/30 bg-rose-500/10 px-2.5 py-1 rounded-full border">
                <span className="h-2 w-2 rounded-full bg-rose-500"></span>
                <span>Backend Offline</span>
              </span>
            )}
          </div>
        </div>

      </div>
    </header>
  );
};
