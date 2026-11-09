import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Layout } from '../components/Layout';
import api from '../api/client';
import {
  FolderKanban,
  FileText,
  BrainCircuit,
  SearchCode,
  CheckSquare,
  Users,
  UploadCloud,
  FileDown,
  UserPlus,
  Trash2,
  ExternalLink
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const ProjectDetails = () => {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showMemberModal, setShowMemberModal] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedRole, setSelectedRole] = useState('Incoming Member');
  const [addingMember, setAddingMember] = useState(false);
  const { user } = useAuth();

  const fetchDetails = async () => {
    try {
      setLoading(true);
      const [projRes, docsRes, usersRes] = await Promise.all([
        api.get(`/projects/${id}`),
        api.get(`/documents/project/${id}`),
        api.get('/auth/users')
      ]);
      setProject(projRes.data);
      setDocuments(docsRes.data);
      setAllUsers(usersRes.data);
    } catch (err) {
      setError('Failed to load project details: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [id]);

  const handleAddMember = async (e) => {
    e.preventDefault();
    if (!selectedUserId) return;
    try {
      setAddingMember(true);
      await api.post(`/projects/${id}/members`, {
        user_id: parseInt(selectedUserId),
        role: selectedRole
      });
      setShowMemberModal(false);
      fetchDetails();
    } catch (err) {
      alert('Failed to add member: ' + (err.response?.data?.detail || err.message));
    } finally {
      setAddingMember(false);
    }
  };

  const handleRemoveMember = async (userId) => {
    if (!window.confirm('Remove this member from project?')) return;
    try {
      await api.delete(`/projects/${id}/members/${userId}`);
      fetchDetails();
    } catch (err) {
      alert('Failed to remove member: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (loading) {
    return (
      <Layout title="Project Details">
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      </Layout>
    );
  }

  if (!project) {
    return (
      <Layout title="Project Details">
        <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center">
          <p className="text-sm font-semibold text-slate-700">Project not found or deleted.</p>
          <Link to="/projects" className="text-xs font-bold text-blue-600 underline mt-2 inline-block">
            Back to Projects
          </Link>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={`Project: ${project.name}`}>
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm font-medium">
          {error}
        </div>
      )}

      {/* Project Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-6 shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200">
                {project.status}
              </span>
              <span className="text-xs text-slate-400">Created: {new Date(project.created_at).toLocaleDateString()}</span>
            </div>
            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">{project.name}</h2>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl">{project.description || 'No description provided.'}</p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Link
              to={`/upload?project_id=${project.id}`}
              className="px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-colors flex items-center gap-1.5 shadow-sm"
            >
              <UploadCloud className="w-4 h-4" />
              Upload Docs
            </Link>
            <Link
              to={`/reports?project_id=${project.id}`}
              className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition-colors flex items-center gap-1.5"
            >
              <FileDown className="w-4 h-4" />
              Handover Report
            </Link>
          </div>
        </div>

        {/* Quick Nav Action Pills */}
        <div className="flex flex-wrap gap-2 mt-6 pt-5 border-t border-slate-100 text-xs font-medium">
          <Link
            to={`/knowledge?project_id=${project.id}`}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200 hover:bg-indigo-100 transition-colors"
          >
            <BrainCircuit className="w-3.5 h-3.5 text-indigo-600" />
            <span>Knowledge Base (<strong>{project.knowledge_count || 0}</strong>)</span>
          </Link>
          <Link
            to={`/gaps?project_id=${project.id}`}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 transition-colors"
          >
            <SearchCode className="w-3.5 h-3.5 text-rose-600" />
            <span>Knowledge Gaps (<strong>{project.gap_count || 0}</strong>)</span>
          </Link>
          <Link
            to={`/approvals?project_id=${project.id}`}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition-colors"
          >
            <CheckSquare className="w-3.5 h-3.5 text-emerald-600" />
            <span>Approvals Queue</span>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Documents List */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-600" />
              <h3 className="text-sm font-bold text-slate-900">Project Documents ({documents.length})</h3>
            </div>
            <Link
              to={`/upload?project_id=${project.id}`}
              className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              Upload New
            </Link>
          </div>

          {documents.length === 0 ? (
            <div className="text-center py-8 border-2 border-dashed border-slate-200 rounded-xl">
              <FileText className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-xs font-semibold text-slate-600">No documents uploaded yet</p>
              <p className="text-[11px] text-slate-400 mt-0.5">Upload PDF, DOCX, or TXT handover files to extract knowledge.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {documents.map((doc) => (
                <div key={doc.id} className="py-3 flex items-center justify-between hover:bg-slate-50 px-2 rounded-lg transition-colors">
                  <div className="flex items-center gap-3">
                    <span className="w-7 h-7 rounded-lg bg-blue-50 text-blue-700 font-bold text-[10px] flex items-center justify-center uppercase">
                      {doc.file_type}
                    </span>
                    <div>
                      <p className="text-xs font-bold text-slate-900 line-clamp-1">{doc.filename}</p>
                      <p className="text-[10px] text-slate-400">
                        {(doc.file_size / 1024).toFixed(1)} KB &bull; {doc.page_count} Page(s) &bull; {doc.knowledge_count || 0} items extracted
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {doc.processing_status}
                    </span>
                    <Link
                      to={`/knowledge?document_id=${doc.id}&project_id=${project.id}`}
                      className="p-1 text-slate-400 hover:text-blue-600 transition-colors"
                      title="View extracted knowledge"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Project Members */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-blue-600" />
              <h3 className="text-sm font-bold text-slate-900">Project Team ({project.members?.length || 0})</h3>
            </div>
            {(user?.role === 'Admin' || user?.role === 'Manager') && (
              <button
                onClick={() => setShowMemberModal(true)}
                className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                <UserPlus className="w-3.5 h-3.5" />
                Add Member
              </button>
            )}
          </div>

          <div className="divide-y divide-slate-100">
            {project.members?.map((m) => (
              <div key={m.id} className="py-2.5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold text-slate-900">{m.user?.full_name || 'Team Member'}</p>
                  <p className="text-[11px] text-blue-600 font-medium">{m.role}</p>
                  <p className="text-[10px] text-slate-400">{m.user?.email}</p>
                </div>
                {(user?.role === 'Admin' || user?.role === 'Manager') && m.user_id !== user.id && (
                  <button
                    onClick={() => handleRemoveMember(m.user_id)}
                    className="text-slate-300 hover:text-red-600 p-1 transition-colors"
                    title="Remove member"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Add Member Modal */}
      {showMemberModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1">Add Team Member</h3>
            <p className="text-xs text-slate-500 mb-4">Assign a user and their continuity role on this project.</p>

            <form onSubmit={handleAddMember} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Select User</label>
                <select
                  required
                  value={selectedUserId}
                  onChange={(e) => setSelectedUserId(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="">-- Choose User --</option>
                  {allUsers.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.full_name} ({u.email})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Project Role</label>
                <select
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="Incoming Member">Incoming Member</option>
                  <option value="Outgoing Member">Outgoing Member</option>
                  <option value="Manager">Manager</option>
                  <option value="Admin">Admin</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowMemberModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addingMember}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow-sm disabled:opacity-50"
                >
                  {addingMember ? 'Adding...' : 'Add to Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Layout>
  );
};
