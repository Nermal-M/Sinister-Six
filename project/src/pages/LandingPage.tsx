import { useNavigate } from 'react-router-dom';
import { Users, Shield } from 'lucide-react';

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <div className="flex justify-center mb-6">
              <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-blue-700 rounded-full flex items-center justify-center shadow-lg">
                <Users className="w-12 h-12 text-white" />
              </div>
            </div>
            <h1 className="text-5xl font-bold text-slate-900 mb-4">
              Complaint Management System
            </h1>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              Register your complaints and track their status in real-time. Our dedicated team is here to help resolve your concerns efficiently.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-12">
            <div className="bg-white rounded-2xl shadow-xl p-8 hover:shadow-2xl transition-shadow duration-300">
              <div className="flex justify-center mb-6">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                  <Users className="w-8 h-8 text-blue-600" />
                </div>
              </div>
              <h2 className="text-2xl font-bold text-slate-900 mb-4 text-center">
                User Portal
              </h2>
              <p className="text-slate-600 mb-8 text-center">
                Register complaints, track status, and communicate with our support team.
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => navigate('/login')}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200"
                >
                  Login
                </button>
                <button
                  onClick={() => navigate('/register')}
                  className="w-full bg-slate-100 hover:bg-slate-200 text-slate-900 font-semibold py-3 px-6 rounded-lg transition-colors duration-200"
                >
                  Register
                </button>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-xl p-8 hover:shadow-2xl transition-shadow duration-300">
              <div className="flex justify-center mb-6">
                <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center">
                  <Shield className="w-8 h-8 text-emerald-600" />
                </div>
              </div>
              <h2 className="text-2xl font-bold text-slate-900 mb-4 text-center">
                Officials Portal
              </h2>
              <p className="text-slate-600 mb-8 text-center">
                Access the administrative dashboard to manage and resolve complaints.
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => navigate('/official-login')}
                  className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200"
                >
                  Officials Login
                </button>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h3 className="text-2xl font-bold text-slate-900 mb-6 text-center">
              How It Works
            </h3>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                  1
                </div>
                <h4 className="font-semibold text-slate-900 mb-2">Register</h4>
                <p className="text-slate-600 text-sm">
                  Create your account to get started
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                  2
                </div>
                <h4 className="font-semibold text-slate-900 mb-2">Submit Complaint</h4>
                <p className="text-slate-600 text-sm">
                  Describe your issue with details
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                  3
                </div>
                <h4 className="font-semibold text-slate-900 mb-2">Track Status</h4>
                <p className="text-slate-600 text-sm">
                  Monitor progress and get updates
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
