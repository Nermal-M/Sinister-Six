import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LandingPage from './pages/LandingPage';
import RegisterPage from './pages/RegisterPage';
import LoginPage from './pages/LoginPage';
import OfficialLoginPage from './pages/OfficialLoginPage';
import UserDashboard from './pages/UserDashboard';
import OfficialDashboard from './pages/OfficialDashboard';

function ProtectedRoute({ children, type }: { children: React.ReactNode; type: 'user' | 'official' }) {
  const { user, userType, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-slate-600">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to={type === 'official' ? '/official-login' : '/login'} />;
  }

  if (userType !== type) {
    return <Navigate to="/" />;
  }

  return <>{children}</>;
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/official-login" element={<OfficialLoginPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute type="user">
                <UserDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/official-dashboard"
            element={
              <ProtectedRoute type="official">
                <OfficialDashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
