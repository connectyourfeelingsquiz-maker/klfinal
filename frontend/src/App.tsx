import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { PredictionForm } from './components/PredictionForm';
import { KL1Results, KL1Candidate } from './components/KL1Results';
import { KLED2Result } from './components/KLED2Result';
import { Footer } from './components/Footer';
import { AlertCircle, History, Clock, Trash2, ArrowUpRight, CheckCircle2 } from 'lucide-react';

// Known default Kerala Lotteries (fallback if network is delayed)
const DEFAULT_LOTTERIES = [
  'Akshaya', 'Bhagyanidhi', 'Bhagyathara', 'Dhanalekshmi',
  'Fifty-Fifty', 'Karunya', 'Karunya Plus', 'Nirmal',
  'Pournami', 'Samrudhi', 'Sthree Sakthi', 'Suvarna Keralam', 'Win Win'
];

interface PredictionResult {
  success: boolean;
  date: string;
  lottery: string;
  kl1: {
    candidates: KL1Candidate[];
  };
  kled2: {
    prediction: string;
  };
  timestamp?: number;
}

export const App: React.FC = () => {
  // Configured Backend URL from environment variable
  const rawApiUrl = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
  
  // App state
  const [date, setDate] = useState<string>(() => {
    // Current date in YYYY-MM-DD
    const now = new Date();
    return now.toISOString().split('T')[0];
  });
  const [lottery, setLottery] = useState<string>('Karunya');
  const [lotteries, setLotteries] = useState<string[]>(DEFAULT_LOTTERIES);
  const [isLoadingLotteries, setIsLoadingLotteries] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [backendStatus, setBackendStatus] = useState<'online' | 'checking' | 'offline'>('checking');
  const [modelsLoaded, setModelsLoaded] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Active prediction results
  const [activeResult, setActiveResult] = useState<PredictionResult | null>(null);

  // Session history (stored in localStorage for session persistence)
  const [history, setHistory] = useState<PredictionResult[]>(() => {
    try {
      const saved = localStorage.getItem('klfinal_session_history');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [activeTab, setActiveTab] = useState<'results' | 'history'>('results');

  // Build endpoint helper
  const getEndpoint = useCallback((path: string) => {
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return rawApiUrl ? `${rawApiUrl}${cleanPath}` : cleanPath;
  }, [rawApiUrl]);

  // Check backend health
  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch(getEndpoint('/api/health'));
      if (res.ok) {
        const data = await res.json();
        setBackendStatus('online');
        setModelsLoaded(Boolean(data.models_loaded));
      } else {
        setBackendStatus('offline');
      }
    } catch {
      setBackendStatus('offline');
    }
  }, [getEndpoint]);

  // Fetch lotteries list
  const fetchLotteries = useCallback(async () => {
    setIsLoadingLotteries(true);
    try {
      const res = await fetch(getEndpoint('/api/lotteries'));
      if (res.ok) {
        const data = await res.json();
        if (data.lotteries && Array.isArray(data.lotteries)) {
          setLotteries(data.lotteries);
          setBackendStatus('online');
          setModelsLoaded(true);
          if (!data.lotteries.includes(lottery) && data.lotteries.length > 0) {
            setLottery(data.lotteries[0]);
          }
        }
      } else {
        await checkHealth();
      }
    } catch (err) {
      console.warn('Could not sync lotteries from backend, using defaults:', err);
      await checkHealth();
    } finally {
      setIsLoadingLotteries(false);
    }
  }, [checkHealth, getEndpoint, lottery]);

  // Initial load
  useEffect(() => {
    fetchLotteries();
  }, [fetchLotteries]);

  // Save history to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('klfinal_session_history', JSON.stringify(history.slice(0, 20)));
    } catch (e) {
      console.warn('Failed to save history to localStorage', e);
    }
  }, [history]);

  // Handle Predict form submit
  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsLoading(true);

    try {
      const response = await fetch(getEndpoint('/api/predict'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          date: date,
          lottery: lottery,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const detailMsg = errorData?.detail || `Prediction request failed with HTTP ${response.status}`;
        throw new Error(detailMsg);
      }

      const data: PredictionResult = await response.json();

      if (!data.success) {
        throw new Error('Prediction API returned an unsuccessful response.');
      }

      const resultWithTimestamp = {
        ...data,
        timestamp: Date.now(),
      };

      setActiveResult(resultWithTimestamp);
      setActiveTab('results');

      // Prepend to session history
      setHistory((prev) => [resultWithTimestamp, ...prev]);
    } catch (err: any) {
      console.error('Prediction failed:', err);
      setErrorMessage(err.message || 'An unexpected error occurred while running prediction models.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    setHistory([]);
    localStorage.removeItem('klfinal_session_history');
  };

  const handleSelectHistoryItem = (item: PredictionResult) => {
    setDate(item.date);
    setLottery(item.lottery);
    setActiveResult(item);
    setActiveTab('results');
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#050814] bg-grid-pattern text-slate-100">
      
      {/* Navigation Header */}
      <Header backendStatus={backendStatus} modelsLoaded={modelsLoaded} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Hero Section Banner */}
        <section className="relative overflow-hidden rounded-3xl p-6 sm:p-10 border border-slate-800 bg-gradient-to-r from-navy-950 via-slate-900 to-navy-900 shadow-2xl">
          <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl -z-0 pointer-events-none" />
          <div className="absolute bottom-0 left-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl -z-0 pointer-events-none" />

          <div className="relative z-10 max-w-3xl space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold uppercase tracking-wider">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Machine Learning Dual Engine
            </div>

            <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-white leading-tight">
              Predictive Intelligence for <br className="hidden sm:block" />
              <span className="bg-gradient-to-r from-cyan-400 via-sky-300 to-blue-500 bg-clip-text text-transparent">
                Kerala Lottery Analytics
              </span>
            </h1>

            <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
              Synthesizing historical draw patterns with two independent ML frameworks:
              <span className="text-cyan-300 font-medium"> KL1 Combinatorial Probability Model</span> and
              <span className="text-indigo-300 font-medium"> KLED2 Cyclical Harmonic Neural Estimator</span>.
            </p>
          </div>

          {/* Quick Metrics Bar */}
          <div className="mt-8 pt-6 border-t border-slate-800/80 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-slate-500 uppercase tracking-wider font-mono block">Models Loaded</span>
              <span className="text-white font-bold text-sm">KL1 & KLED2 (12 Trees)</span>
            </div>
            <div>
              <span className="text-slate-500 uppercase tracking-wider font-mono block">Digit Architecture</span>
              <span className="text-cyan-400 font-bold text-sm">6 Discrete Estimators</span>
            </div>
            <div>
              <span className="text-slate-500 uppercase tracking-wider font-mono block">Lotteries Supported</span>
              <span className="text-indigo-400 font-bold text-sm">{lotteries.length} Official Lotteries</span>
            </div>
            <div>
              <span className="text-slate-500 uppercase tracking-wider font-mono block">Feature Encoding</span>
              <span className="text-emerald-400 font-bold text-sm">Harmonic Sin / Cos</span>
            </div>
          </div>
        </section>

        {/* Error Alert Box */}
        {errorMessage && (
          <div className="rounded-2xl border border-rose-500/40 bg-rose-500/10 p-5 flex items-start space-x-3.5 text-rose-200">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-bold text-rose-300 text-sm">Inference or Connection Error</h4>
              <p className="text-xs sm:text-sm mt-0.5">{errorMessage}</p>
              <div className="mt-2 text-xs font-mono text-rose-400/80">
                Ensure backend API is running at <code className="bg-rose-950/60 px-2 py-0.5 rounded">{getEndpoint('/api/health')}</code>
              </div>
            </div>
          </div>
        )}

        {/* Input Form Section */}
        <section>
          <PredictionForm
            date={date}
            setDate={setDate}
            lottery={lottery}
            setLottery={setLottery}
            lotteries={lotteries}
            isLoadingLotteries={isLoadingLotteries}
            onRefreshLotteries={fetchLotteries}
            onSubmit={handlePredict}
            isLoading={isLoading}
            backendStatus={backendStatus}
          />
        </section>

        {/* Tab switcher: Active Results vs Session History */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setActiveTab('results')}
              className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                activeTab === 'results'
                  ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              Dual Model Predictions
            </button>

            <button
              onClick={() => setActiveTab('history')}
              className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === 'history'
                  ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <History className="w-4 h-4" />
              <span>Session History</span>
              {history.length > 0 && (
                <span className="px-1.5 py-0.5 rounded-full text-xs font-mono bg-slate-800 text-slate-300 border border-slate-700">
                  {history.length}
                </span>
              )}
            </button>
          </div>

          {activeTab === 'history' && history.length > 0 && (
            <button
              onClick={handleClearHistory}
              className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1 px-2.5 py-1 rounded-lg hover:bg-rose-500/10 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear History</span>
            </button>
          )}
        </div>

        {/* Tab 1: Predictions Results View */}
        {activeTab === 'results' && (
          <div>
            {activeResult ? (
              <div className="space-y-6">
                
                {/* Result header banner */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                  <div className="flex items-center gap-3">
                    <span className="w-3 h-3 rounded-full bg-cyan-400 animate-pulse" />
                    <div>
                      <span className="text-xs text-slate-400 uppercase tracking-wider block">Target Draw</span>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-base">{activeResult.lottery}</span>
                        <span className="text-slate-500 font-mono text-sm">•</span>
                        <span className="font-mono text-cyan-300 text-sm font-semibold">{activeResult.date}</span>
                      </div>
                    </div>
                  </div>

                  <span className="text-xs text-slate-500 font-mono">
                    Generated: {new Date(activeResult.timestamp || Date.now()).toLocaleTimeString()}
                  </span>
                </div>

                {/* Dual Results Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
                  
                  {/* KL1 Column */}
                  <div className="h-full">
                    <KL1Results
                      candidates={activeResult.kl1.candidates}
                      date={activeResult.date}
                      lottery={activeResult.lottery}
                    />
                  </div>

                  {/* KLED2 Column */}
                  <div className="h-full">
                    <KLED2Result
                      prediction={activeResult.kled2.prediction}
                      date={activeResult.date}
                      lottery={activeResult.lottery}
                    />
                  </div>

                </div>

              </div>
            ) : (
              /* Empty state before first prediction */
              <div className="glass-panel rounded-2xl p-12 text-center border border-slate-800/80 my-8">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-800/80 border border-slate-700/80 flex items-center justify-center text-slate-400">
                  <Clock className="w-8 h-8 text-cyan-400/80 animate-pulse" />
                </div>
                <h3 className="text-lg font-bold text-white">No Predictions Generated Yet</h3>
                <p className="text-sm text-slate-400 max-w-md mx-auto mt-1">
                  Select a draw date and Kerala lottery above, then click <strong className="text-cyan-400">Predict Results</strong> to query both KL1 and KLED2 machine learning models simultaneously.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Session History View */}
        {activeTab === 'history' && (
          <div className="space-y-4">
            {history.length === 0 ? (
              <div className="glass-panel rounded-2xl p-12 text-center border border-slate-800/80">
                <History className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                <h4 className="font-semibold text-slate-300 text-base">No Prediction History</h4>
                <p className="text-xs text-slate-500 mt-1">
                  Your predictions generated during this session will be listed here.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {history.map((item, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleSelectHistoryItem(item)}
                    className="glass-panel-interactive rounded-xl p-5 border border-slate-800 cursor-pointer group flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between text-xs mb-2">
                        <span className="font-bold text-cyan-400 uppercase tracking-wider">{item.lottery}</span>
                        <span className="font-mono text-slate-500">{item.date}</span>
                      </div>

                      <div className="space-y-2 my-3">
                        <div className="flex items-center justify-between text-xs bg-slate-900/80 px-2.5 py-1.5 rounded-lg border border-slate-800">
                          <span className="text-slate-400 font-mono">KL1 Top #1:</span>
                          <span className="font-mono font-bold text-white tracking-wider">
                            {item.kl1.candidates[0]?.candidate || 'N/A'}
                          </span>
                        </div>

                        <div className="flex items-center justify-between text-xs bg-slate-900/80 px-2.5 py-1.5 rounded-lg border border-slate-800">
                          <span className="text-slate-400 font-mono">KLED2 Cons.:</span>
                          <span className="font-mono font-bold text-indigo-300 tracking-wider">
                            {item.kled2.prediction}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                      <span>{item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : ''}</span>
                      <span className="text-cyan-400 group-hover:underline flex items-center gap-0.5 font-medium">
                        View Results <ArrowUpRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

      </main>

      {/* Footer */}
      <Footer />

    </div>
  );
};

export default App;
