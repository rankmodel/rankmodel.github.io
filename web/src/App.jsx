import { Routes, Route } from 'react-router-dom'
import AuroraBackground from './components/AuroraBackground.jsx'
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

export default function App() {
  return (
    <div className="mr-app">
      <AuroraBackground />
      <Nav />
      <main className="mr-main">
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
