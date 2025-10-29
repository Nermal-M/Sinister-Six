import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { supabase, Complaint, Profile } from '../lib/supabase';
import { LogOut, Plus, FileText, Clock, CheckCircle, XCircle, Phone } from 'lucide-react';

export default function UserDashboard() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewComplaint, setShowNewComplaint] = useState(false);
  const [showCallCenter, setShowCallCenter] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '',
  });

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    loadData();
  }, [user, navigate]);

  async function loadData() {
    try {
      const { data: profileData } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', user!.id)
        .single();

      if (profileData) {
        setProfile(profileData);
      }

      const { data: complaintsData } = await supabase
        .from('complaints')
        .select('*')
        .eq('user_id', user!.id)
        .order('created_at', { ascending: false });

      if (complaintsData) {
        setComplaints(complaintsData);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmitComplaint(e: React.FormEvent) {
    e.preventDefault();

    try {
      const { error } = await supabase
        .from('complaints')
        .insert({
          user_id: user!.id,
          title: formData.title,
          description: formData.description,
          category: formData.category,
        });

      if (error) throw error;

      setFormData({ title: '', description: '', category: '' });
      setShowNewComplaint(false);
      loadData();
    } catch (error) {
      console.error('Error submitting complaint:', error);
    }
  }

  async function handleSignOut() {
    await signOut();
    navigate('/');
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-slate-100 text-slate-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4" />;
      case 'in_progress':
        return <Clock className="w-4 h-4" />;
      case 'pending':
        return <FileText className="w-4 h-4" />;
      default:
        return <XCircle className="w-4 h-4" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-slate-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <nav className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">User Dashboard</h1>
              <p className="text-slate-600">Welcome, {profile?.full_name || profile?.email}</p>
            </div>
            <button
              onClick={handleSignOut}
              className="flex items-center gap-2 px-4 py-2 text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <LogOut className="w-5 h-5" />
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <button
            onClick={() => setShowNewComplaint(true)}
            className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow text-left"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <Plus className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Register Complaint</h3>
                <p className="text-sm text-slate-600">Submit a new complaint</p>
              </div>
            </div>
          </button>

          <button
            onClick={() => setShowCallCenter(true)}
            className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow text-left"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center">
                <Phone className="w-6 h-6 text-emerald-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Call Center</h3>
                <p className="text-sm text-slate-600">Contact support via phone</p>
              </div>
            </div>
          </button>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-slate-900 mb-4">Your Complaints</h2>

          {complaints.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">No complaints registered yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {complaints.map((complaint) => (
                <div key={complaint.id} className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-slate-900">{complaint.title}</h3>
                    <span className={`flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(complaint.status)}`}>
                      {getStatusIcon(complaint.status)}
                      {complaint.status.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="text-slate-600 text-sm mb-3">{complaint.description}</p>
                  <div className="flex gap-4 text-xs text-slate-500">
                    <span>Category: {complaint.category}</span>
                    <span>Priority: {complaint.priority}</span>
                    <span>Date: {new Date(complaint.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {showNewComplaint && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-2xl font-bold text-slate-900 mb-6">Register New Complaint</h3>
            <form onSubmit={handleSubmitComplaint} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Title</label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  placeholder="Brief title of your complaint"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Category</label>
                <select
                  required
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                >
                  <option value="">Select a category</option>
                  <option value="Technical">Technical</option>
                  <option value="Billing">Billing</option>
                  <option value="Service">Service</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Description</label>
                <textarea
                  required
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={4}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none"
                  placeholder="Describe your complaint in detail"
                />
              </div>

              <div className="flex gap-3">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                >
                  Submit
                </button>
                <button
                  type="button"
                  onClick={() => setShowNewComplaint(false)}
                  className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-900 font-semibold py-2 px-4 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showCallCenter && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Phone className="w-8 h-8 text-emerald-600" />
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-4">Call Center Support</h3>
              <p className="text-slate-600 mb-6">Our support team is available in multiple regional languages to assist you.</p>

              <div className="bg-slate-50 rounded-lg p-4 mb-6">
                <p className="text-sm text-slate-600 mb-2">Call us at:</p>
                <p className="text-2xl font-bold text-slate-900">1-800-SUPPORT</p>
                <p className="text-sm text-slate-600 mt-2">Available 24/7</p>
              </div>

              <button
                onClick={() => setShowCallCenter(false)}
                className="w-full bg-slate-100 hover:bg-slate-200 text-slate-900 font-semibold py-2 px-4 rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
