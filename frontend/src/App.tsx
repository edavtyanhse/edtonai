import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import { WizardPage, History, Compare, Workspace, IdealResumePage, LoginPage, RegisterPage } from './pages'
import VerifyEmailPage from './pages/auth/VerifyEmailPage'
import OAuthCallbackPage from './pages/auth/OAuthCallbackPage'
import LandingPage from './pages/LandingPage'
import { Toaster } from './components/Toast'
import { AuthProvider } from './context/AuthContext'
import RequireAuth from './components/RequireAuth'

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/oauth/callback" element={<OAuthCallbackPage />} />

        {/* Protected routes */}
        <Route path="/wizard" element={
          <RequireAuth>
            <WizardPage />
          </RequireAuth>
        } />

        <Route path="/ideal-resume" element={
          <RequireAuth>
            <IdealResumePage />
          </RequireAuth>
        } />

        <Route element={<Layout />}>
          <Route path="workspace" element={
            <RequireAuth>
              <Workspace />
            </RequireAuth>
          } />
          <Route path="history" element={
            <RequireAuth>
              <History />
            </RequireAuth>
          } />
          <Route path="compare" element={
            <RequireAuth>
              <Compare />
            </RequireAuth>
          } />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster />
    </AuthProvider>
  )
}

export default App
