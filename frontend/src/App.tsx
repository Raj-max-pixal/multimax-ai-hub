import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import { useAuth } from './contexts/AuthContext'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const AIChat = lazy(() => import('./pages/AIChat'))
const AICoding = lazy(() => import('./pages/AICoding'))
const Research = lazy(() => import('./pages/Research'))
const Agents = lazy(() => import('./pages/Agents'))
const Memory = lazy(() => import('./pages/Memory'))
const Automation = lazy(() => import('./pages/Automation'))
const PDFChat = lazy(() => import('./pages/PDFChat'))
const VoiceAssistant = lazy(() => import('./pages/VoiceAssistant'))
const AIImage = lazy(() => import('./pages/AIImage'))
const VideoStudio = lazy(() => import('./pages/VideoStudio'))
const Plugins = lazy(() => import('./pages/Plugins'))
const TeamWorkspace = lazy(() => import('./pages/TeamWorkspace'))
const CommunityMarketplace = lazy(() => import('./pages/CommunityMarketplace'))
const MobileApps = lazy(() => import('./pages/MobileApps'))
const Enterprise = lazy(() => import('./pages/Enterprise'))
const Settings = lazy(() => import('./pages/Settings'))
const Login = lazy(() => import('./pages/Login'))
const Signup = lazy(() => import('./pages/Signup'))
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'))
const Profile = lazy(() => import('./pages/Profile'))

function PageLoader() {
  return (
    <div className="min-h-[40vh] flex items-center justify-center text-slate-400">
      <span className="animate-pulse">Loading...</span>
    </div>
  )
}

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
      <Suspense fallback={<PageLoader />}>
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
      </Suspense>
    </BrowserRouter>
  )
}

export default App
