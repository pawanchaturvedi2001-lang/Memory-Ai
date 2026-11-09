import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Layout } from '../components/Layout';
import api from '../api/client';
import {
  CheckSquare,
  CheckCircle2,
  XCircle,
  Edit3,
  Clock,
  MessageSquare,
  FileText,
  User,
  ShieldCheck,
  AlertTriangle
} from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';
import { useAuth } from '../context/AuthContext';

export const ApprovalManagement = () => {
  const [searchParams] = useSearchParams();
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(searchParams.get('project_id') || '');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reviewModalItem, setReviewModalItem] = useState(null);
  const [actionType, setActionType] = useState('APPROVE'); // 'APPROVE' or 'REJECT'
  const [reviewComment, setReviewComment] = useState('');
  const [editedTitle, setEditedTitle] = useState('');
  const [editedContent, setEditedContent] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const res = await api.get('/projects');
        setProjects(res.data);
      } catch (err) {
        console.error('Failed to load projects', err);
      }
    };
    fetchProjects();
  }, []);

  const fetchApprovals = async () => {
    try {
      setLoading(true);
      let url = '/approvals';
      if (selectedProjectId) {
        url += `?project_id=${selectedProjectId}`;
      }
      const res = await api.get(url);
      setItems(res.data);
    } catch (err) {
      setError('Failed to fetch approvals queue: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, [selectedProjectId]);

  const openReviewModal = (item, action) => {
    setReviewModalItem(item);
    setActionType(action);
    setEditedTitle(item.title);
    setEditedContent(item.content);
    setReviewComment('');
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    if (!reviewModalItem) return;

    try {
      setSubmitting(true);
      await api.patch(`/approvals/${reviewModalItem.id}`, {
        action: actionType,
        review_comment: reviewComment,
        edited_title: editedTitle,
        edited_content: editedContent
      });
      setReviewModalItem(null);
      fetchApprovals();
    } catch (err) {
      alert('Review submission failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Layout title="Human Review & Approval Governance">
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">Continuity Verification Queue</h2>
          <p className="text-xs text-slate-500">
            Human-in-the-loop review. Approve or reject AI-extracted claims before publishing to incoming team members.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="text-xs font-semibold px-3 py-2 rounded-xl border border-slate-200 bg-white focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : items.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
          <ShieldCheck className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-900">Review Queue Cleared</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
            All extracted items have been reviewed, audited, and approved for handover.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-2xl border border-slate-200 p-5 shadow-2xs hover:border-slate-300 transition-all"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2.5">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-700">
                    {item.type.replace('_', ' ')}
                  </span>
                  <StatusBadge status={item.status} />
                  <span className="text-xs text-slate-400 font-medium">#{item.id}</span>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => openReviewModal(item, 'APPROVE')}
                    className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1 shadow-2xs transition-colors"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Approve
                  </button>
                  <button
                    onClick={() => openReviewModal(item, 'REJECT')}
                    className="px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-bold text-xs flex items-center gap-1 transition-colors"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    Reject
                  </button>
                </div>
              </div>

              <h3 className="text-sm font-bold text-slate-900 mb-1">{item.title}</h3>
              <p className="text-xs text-slate-700 leading-relaxed mb-3">{item.content}</p>

              {/* Source Footnote */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-slate-500">
                  <FileText className="w-3.5 h-3.5 text-blue-500" />
                  <span>Document: <strong>{item.document_filename || 'System Document'}</strong></span>
                </div>
                {item.evidence && (
                  <span className={item.evidence.is_verified ? 'text-emerald-700 font-bold text-[11px]' : 'text-rose-600 font-bold text-[11px]'}>
                    {item.evidence.is_verified ? '✓ Verified Source Quote' : '⚠ Missing Verbatim Match'}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Review & Edit Modal */}
      {reviewModalItem && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1">
              {actionType === 'APPROVE' ? 'Approve Knowledge Item' : 'Reject Knowledge Item'}
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Add your sign-off comments, review timestamps, and edit content if needed.
            </p>

            <form onSubmit={handleReviewSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Title</label>
                <input
                  type="text"
                  value={editedTitle}
                  onChange={(e) => setEditedTitle(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Content (Editable)</label>
                <textarea
                  rows={4}
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Reviewer Note / Comment</label>
                <input
                  type="text"
                  placeholder="e.g. Verified with outgoing lead engineer Sarah on Nov 9"
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setReviewModalItem(null)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className={`px-4 py-2 rounded-lg text-xs font-bold text-white shadow-sm disabled:opacity-50 ${
                    actionType === 'APPROVE' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-rose-600 hover:bg-rose-700'
                  }`}
                >
                  {submitting ? 'Recording...' : `Confirm ${actionType}`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Layout>
  );
};
