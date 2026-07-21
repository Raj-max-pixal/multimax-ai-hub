import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import AIChat from './pages/AIChat'
import AICoding from './pages/AICoding'
import Research from './pages/Research'
import Agents from './pages/Agents'
import Memory from './pages/Memory'
import Automation from './pages/Automation'
import PDFChat from './pages/PDFChat'
import VoiceAssistant from './pages/VoiceAssistant'
import AIImage from './pages/AIImage'
import VideoStudio from './pages/VideoStudio'
import Plugins from './pages/Plugins'
import TeamWorkspace from './pages/TeamWorkspace'
import CommunityMarketplace from './pages/CommunityMarketplace'
import MobileApps from './pages/MobileApps'
import Enterprise from './pages/Enterprise'
import Settings from './pages/Settings'
import Login from './pages/Login'
import Signup from './pages/Signup'
import ForgotPassword from './pages/ForgotPassword'
import Profile from './pages/Profile'
import ProtectedRoute from './components/ProtectedRoute'
import { useAuth } from './contexts/AuthContext'

function App() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 bg-gradient-to-br from-green-400 to-green-600 rounded-2xl flex items-center justify-center">
            <span className="text-3xl font-bold text-white">M</span>
          </div>
          <p className="text-slate-400 animate-pulse">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
        <Route path="/signup" element={user ? <Navigate to="/" replace /> : <Signup />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        
        <Route path="/*" element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/chat" element={<AIChat />} />
                <Route path="/pdf" element={<PDFChat />} />
                <Route path="/coding" element={<AICoding />} />
                <Route path="/research" element={<Research />} />
                <Route path="/agents" element={<Agents />} />
                <Route path="/memory" element={<Memory />} />
                <Route path="/automation" element={<Automation />} />
                <Route path="/voice" element={<VoiceAssistant />} />
                <Route path="/image" element={<AIImage />} />
                <Route path="/video" element={<VideoStudio />} />
                <Route path="/plugins" element={<Plugins />} />
                <Route path="/team" element={<TeamWorkspace />} />
                <Route path="/marketplace" element={<CommunityMarketplace />} />
                <Route path="/mobile" element={<MobileApps />} />
                <Route path="/enterprise" element={<Enterprise />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  )
}

export default App
