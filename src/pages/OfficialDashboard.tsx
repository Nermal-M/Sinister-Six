import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { supabase, Complaint, Official } from '../lib/supabase';
import { LogOut, FileText, Filter, ChevronDown } from 'lucide-react';

export default function OfficialDashboard() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [official, setOfficial] = useState<Official | null>(null);
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [filteredComplaints, setFilteredComplaints] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [showAllComplaints, setShowAllComplaints] = useState(true);

  useEffect(() => {
    if (!user) {
      navigate('/official-login');
      return;
    }
    loadData();
  }, [user, navigate]);

  useEffect(() => {
    filterComplaints();
  }, [complaints, categoryFilter, showAllComplaints]);

  async function loadData() {
    try {
      const { data: officialData } = await supabase
        .from('officials')
        .select('*')
        .eq('id', user!.id)
        .single();

      if (officialData) {
        setOfficial(officialData);
      }

      const { data: complaintsData } = await supabase
        .from('complaints')
        .select('*')
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

  function filterComplaints() {
    let filtered = [...complaints];

    if (categoryFilter !== 'all') {
      filtered = filtered.filter(c => c.category === categoryFilter);
    }

    if (!showAllComplaints) {
      filtered = filtered.slice(0, 10);
    }

    setFilteredComplaints(filtered);
  }

  async function updateComplaintStatus(complaintId: string, newStatus: string) {
    try {
      const { error } = await supabase
        .from('complaints')
        .update({ status: newStatus, updated_at: new Date().toISOString() })
        .eq('id', complaintId);

      if (error) throw error;

      loadData();
    } catch (error) {
      console.error('Error updating complaint:', error);
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

  const stats = {
    total: complaints.length,
    pending: complaints.filter(c => c.status === 'pending').length,
    inProgress: complaints.filter(c => c.status === 'in_progress').length,
    completed: complaints.filter(c => c.status === 'completed').length,
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
              <h1 className="text-2xl font-bold text-slate-900">Official Dashboard</h1>
              <p className="text-slate-600">Welcome, {official?.full_name}</p>
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
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6">
            <p className="text-slate-600 text-sm mb-1">Total Complaints</p>
            <p className="text-3xl font-bold text-slate-900">{stats.total}</p>
          </div>
          <div className="bg-white rounded-xl shadow-md p-6">
            <p className="text-slate-600 text-sm mb-1">Pending</p>
            <p className="text-3xl font-bold text-yellow-600">{stats.pending}</p>
          </div>
          <div className="bg-white rounded-xl shadow-md p-6">
            <p className="text-slate-600 text-sm mb-1">In Progress</p>
            <p className="text-3xl font-bold text-blue-600">{stats.inProgress}</p>
          </div>
          <div className="bg-white rounded-xl shadow-md p-6">
            <p className="text-slate-600 text-sm mb-1">Completed</p>
            <p className="text-3xl font-bold text-green-600">{stats.completed}</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6 mb-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-slate-600" />
              <span className="font-medium text-slate-700">Filters:</span>
            </div>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
            >
              <option value="all">All Categories</option>
              <option value="Technical">Technical</option>
              <option value="Billing">Billing</option>
              <option value="Service">Service</option>
              <option value="Other">Other</option>
            </select>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showAllComplaints}
                onChange={(e) => setShowAllComplaints(e.target.checked)}
                className="w-4 h-4 text-emerald-600 rounded focus:ring-emerald-500"
              />
              <span className="text-slate-700">Show all complaints</span>
            </label>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-slate-900 mb-4">
            Complaint Management
          </h2>

          {filteredComplaints.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">No complaints found</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredComplaints.map((complaint) => (
                <div key={complaint.id} className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <h3 className="font-semibold text-slate-900 mb-1">{complaint.title}</h3>
                      <p className="text-slate-600 text-sm mb-2">{complaint.description}</p>
                      <div className="flex flex-wrap gap-3 text-xs text-slate-500">
                        <span className="bg-slate-100 px-2 py-1 rounded">Category: {complaint.category}</span>
                        <span className="bg-slate-100 px-2 py-1 rounded">Priority: {complaint.priority}</span>
                        <span className="bg-slate-100 px-2 py-1 rounded">Date: {new Date(complaint.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(complaint.status)}`}>
                        {complaint.status.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => updateComplaintStatus(complaint.id, 'pending')}
                      disabled={complaint.status === 'pending'}
                      className="px-3 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Mark Pending
                    </button>
                    <button
                      onClick={() => updateComplaintStatus(complaint.id, 'in_progress')}
                      disabled={complaint.status === 'in_progress'}
                      className="px-3 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Mark In Progress
                    </button>
                    <button
                      onClick={() => updateComplaintStatus(complaint.id, 'completed')}
                      disabled={complaint.status === 'completed'}
                      className="px-3 py-1 text-xs font-medium bg-green-100 text-green-800 rounded hover:bg-green-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Mark Completed
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {!showAllComplaints && complaints.length > 10 && (
            <div className="mt-4 text-center">
              <button
                onClick={() => setShowAllComplaints(true)}
                className="text-emerald-600 hover:text-emerald-700 font-medium flex items-center gap-1 mx-auto"
              >
                Show more complaints
                <ChevronDown className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
