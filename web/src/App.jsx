import { lazy, Suspense, useEffect } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import Nav from './components/Nav.jsx'
import Footer from './components/Footer.jsx'
import Leaderboard from './pages/Leaderboard.jsx'
import ModelDetail from './pages/ModelDetail.jsx'
import Collections from './pages/Collections.jsx'
import HeadToHead from './pages/HeadToHead.jsx'
import Quiz from './pages/Quiz.jsx'
import Methodology from './pages/Methodology.jsx'
import Pricing from './pages/Pricing.jsx'
import Api from './pages/Api.jsx'

const AuroraBackground = lazy(() => import('./components/AuroraBackground.jsx'))

const TITLES = {
  '/': 'ModelRank — Independent HuggingFace Model Leaderboard',
  '/collections': 'Collections — ModelRank',
  '/head-to-head': 'Head to Head — ModelRank',
  '/quiz': 'Model Quiz — ModelRank',
  '/methodology': 'Methodology — ModelRank',
  '/pricing': 'Pricing — ModelRank',
  '/api': 'API — ModelRank',
}

export default function App() {
  const location = useLocation()

  useEffect(() => {
    if (location.pathname.startsWith('/model/')) {
      document.title = 'Model · ModelRank'
    } else {
      document.title = TITLES[location.pathname] || 'ModelRank'
    }
  }, [location.pathname])

  return (
    <div className="mr-app">
      <a href="#main-content" className="skip-link">Skip to content</a>
      <Suspense fallback={null}>
        <AuroraBackground />
      </Suspense>
      <Nav />
      <main className="mr-main" id="main-content">
        <Routes>
          <Route path="/" element={<Leaderboard />} />
          <Route path="/model/:id" element={<ModelDetail />} />
          <Route path="/collections" element={<Collections />} />
          <Route path="/head-to-head" element={<HeadToHead />} />
          <Route path="/quiz" element={<Quiz />} />
          <Route path="/methodology" element={<Methodology />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/api" element={<Api />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
