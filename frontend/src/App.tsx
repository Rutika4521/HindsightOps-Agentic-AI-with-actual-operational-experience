import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import InvestigatePage from './pages/InvestigatePage';
import MemoryExplorerPage from './pages/MemoryExplorerPage';
import DemoPage from './pages/DemoPage';
import { Brain, Search, Zap } from 'lucide-react';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
        {/* ── Header ── */}
        <header className="bg-gray-900 border-b border-gray-800 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-blue-600 rounded-lg p-2">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white tracking-tight">
                  Incident Memory Commander
                </h1>
                <p className="text-xs text-gray-400">An AI investigator that learns from what actually happened</p>
              </div>
            </div>
            <nav className="flex items-center gap-1">
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`
                }
              >
                <Search className="w-4 h-4" />
                Investigate
              </NavLink>
              <NavLink
                to="/memory"
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`
                }
              >
                <Brain className="w-4 h-4" />
                Memory Explorer
              </NavLink>
              <NavLink
                to="/demo"
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-orange-600 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`
                }
              >
                <Zap className="w-4 h-4" />
                Demo Controls
              </NavLink>
            </nav>
          </div>
        </header>

        {/* ── Main ── */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8">
          <Routes>
            <Route path="/" element={<InvestigatePage />} />
            <Route path="/memory" element={<MemoryExplorerPage />} />
            <Route path="/demo" element={<DemoPage />} />
          </Routes>
        </main>

        {/* ── Footer ── */}
        <footer className="border-t border-gray-800 py-4 text-center text-xs text-gray-600">
          Powered by{' '}
          <a href="https://hindsight.vectorize.io" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:text-blue-400">
            Hindsight
          </a>{' '}
          persistent memory · Groq LLM
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
