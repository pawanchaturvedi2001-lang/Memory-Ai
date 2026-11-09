import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Layout } from '../components/Layout';
import api from '../api/client';
import {
  BrainCircuit,
  Filter,
  FileText,
  Search,
  Quote,
  CheckCircle2,
  AlertTriangle,
  Info,
  ChevronDown,
  Sparkles,
  ShieldCheck
} from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';
import { useAuth } from '../context/AuthContext';

export const KnowledgeExtraction = () => {
  const [searchParams] = useSearchParams();
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(searchParams.get('project_id') || '');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedType, setSelectedType] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeEvidenceModal, setActiveEvidenceModal] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const res = await api.get('/projects');
        setProjects(res.data);
        if (!selectedProjectId && res.data.length > 0) {
          setSelectedProjectId(res.data[0].id.toString());
        }
      } catch (err) {
        console.error('Failed to load projects', err);
      }
    };
    fetchProjects();
  }, []);

  const fetchKnowledge = async () => {
    if (!selectedProjectId) return;
    try {
      setLoading(true);
      let url = `/knowledge/${selectedProjectId}`;
      const params = [];
      if (selectedStatus !== 'ALL') params.push(`status=${encodeURIComponent(selectedStatus)}`);
      if (selectedType !== 'ALL') params.push(`type=${encodeURIComponent(selectedType)}`);
      if (params.length > 0) url += `?${params.join('&')}`;

      const res = await api.get(url);
      setItems(res.data);
    } catch (err) {
      setError('Failed to fetch knowledge items: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKnowledge();
  }, [selectedProjectId, selectedType, selectedStatus]);

  const filteredItems = items.filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.title?.toLowerCase().includes(q) ||
      item.content?.toLowerCase().includes(q) ||
      item.type?.toLowerCase().includes(q)
    );
  });

  const categories = [
    { id: 'ALL', label: 'All Knowledge Types' },
    { id: 'technical_decision', label: 'Technical Decisions' },
    { id: 'pending_task', label: 'Pending Tasks' },
    { id: 'unresolved_bug', label: 'Unresolved Bugs' },
    { id: 'project_risk', label: 'Project Risks' },
    { id: 'dependency', label: 'Dependencies' },
    { id: 'tech_stack', label: 'Tech Stack' },
    { id: 'architecture', label: 'Architecture' },
    { id: 'context', label: 'Project Context' }
  ];

  return (
    <Layout title="Knowledge Base & Evidence Grounding">
      {/* Top Filter Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 mb-6 shadow-2xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 flex-1 min-w-[280px]">
          {/* Project Selector */}
          <div className="min-w-[220px]">
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="w-full text-xs font-semibold px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  Project: {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Search Box */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search knowledge claims, decisions, bugs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="text-xs font-medium px-3 py-2 rounded-xl border border-slate-200 bg-white focus:ring-2 focus:ring-blue-500"
          >
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="text-xs font-medium px-3 py-2 rounded-xl border border-slate-200 bg-white focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="SUPPORTED">SUPPORTED</option>
            <option value="NEEDS REVIEW">NEEDS REVIEW</option>
            <option value="CONFLICTING">CONFLICTING</option>
            <option value="MISSING EVIDENCE">MISSING EVIDENCE</option>
            <option value="UNRESOLVED">UNRESOLVED</option>
            <option value="APPROVED">APPROVED</option>
            <option value="REJECTED">REJECTED</option>
          </select>
        </div>
      </div>

      {user?.role === 'Incoming Member' && (
        <div className="mb-4 p-3 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 text-xs flex items-center gap-2 font-medium">
          <Info className="w-4 h-4 text-blue-600 shrink-0" />
          <span>Role view active: As an Incoming Member, only verified and approved knowledge authorized for continuity is displayed.</span>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
          <BrainCircuit className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-900">No Knowledge Items Found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
            No items match your filter criteria. Ingest documents or reset demo data to extract knowledge items.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredItems.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-2xl border border-slate-200 p-5 shadow-2xs hover:border-slate-300 transition-all"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2.5">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-700">
                    {item.type.replace('_', ' ')}
                  </span>
                  <StatusBadge status={item.status} />
                  <span className="text-[11px] text-slate-400 font-medium">
                    ID #{item.id}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-400 text-[11px]">Confidence:</span>
                  <div className="w-16 bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-blue-600 h-full rounded-full"
                      style={{ width: `${Math.round(item.confidence * 100)}%` }}
                    ></div>
                  </div>
                  <span className="font-bold text-slate-700 text-[11px]">
                    {Math.round(item.confidence * 100)}%
                  </span>
                </div>
              </div>

              <h3 className="text-base font-bold text-slate-900 mb-1.5">{item.title}</h3>
              <p className="text-xs text-slate-700 leading-relaxed">{item.content}</p>

              {/* Task Details Sub-Card if Task */}
              {item.task_details && (
                <div className="mt-3 p-3 bg-slate-50 rounded-xl border border-slate-100 flex flex-wrap items-center gap-4 text-xs">
                  <div>
                    <span className="text-slate-400 text-[11px] block">Owner / Assignee</span>
                    <strong className={item.task_details.owner ? 'text-slate-800' : 'text-rose-600 font-bold'}>
                      {item.task_details.owner || 'UNASSIGNED'}
                    </strong>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[11px] block">Deadline</span>
                    <strong className={item.task_details.deadline ? 'text-slate-800' : 'text-amber-600 font-bold'}>
                      {item.task_details.deadline || 'MISSING DEADLINE'}
                    </strong>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[11px] block">Priority</span>
                    <span className="font-bold text-slate-700">{item.task_details.priority}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[11px] block">Execution Status</span>
                    <span className="font-bold text-slate-700">{item.task_details.status}</span>
                  </div>
                </div>
              )}

              {/* Evidence Traceability Footnote */}
              <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between text-xs gap-2">
                <div className="flex items-center gap-2 text-slate-500">
                  <FileText className="w-3.5 h-3.5 text-blue-500" />
                  <span>
                    Source: <strong className="text-slate-700">{item.document_filename || 'System Spec'}</strong>
                  </span>
                  {item.evidence && (
                    <span className="text-slate-400">&bull; Page {item.evidence.page_number}</span>
                  )}
                </div>

                {item.evidence ? (
                  <button
                    onClick={() => setActiveEvidenceModal(item)}
                    className="flex items-center gap-1.5 font-bold text-blue-600 hover:text-blue-700 text-xs"
                  >
                    <Quote className="w-3.5 h-3.5" />
                    Inspect Verbatim Evidence
                  </button>
                ) : (
                  <span className="text-rose-600 text-[11px] font-medium flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" /> No source citation linked
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Evidence Modal */}
      {activeEvidenceModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-blue-600" />
                <h3 className="text-base font-bold text-slate-900">Source Evidence Traceability</h3>
              </div>
              <button
                onClick={() => setActiveEvidenceModal(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <span className="text-slate-400 font-semibold block mb-0.5">Knowledge Claim</span>
                <p className="font-bold text-slate-900 text-sm">{activeEvidenceModal.title}</p>
              </div>

              <div>
                <span className="text-slate-400 font-semibold block mb-0.5">Source Document & Location</span>
                <p className="font-medium text-slate-700">
                  {activeEvidenceModal.document_filename || 'Unknown Document'} &bull; Page {activeEvidenceModal.evidence?.page_number || 1}
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-slate-400 font-semibold block mb-1 uppercase tracking-wider text-[10px]">
                  Verbatim Excerpt from Source Document
                </span>
                <blockquote className="italic text-slate-800 text-xs border-l-2 border-blue-500 pl-3 py-1">
                  "{activeEvidenceModal.evidence?.exact_quote}"
                </blockquote>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                <div>
                  <span className="text-slate-400 text-[11px] block">Verification Status</span>
                  <span className={activeEvidenceModal.evidence?.is_verified ? 'text-emerald-700 font-bold' : 'text-rose-600 font-bold'}>
                    {activeEvidenceModal.evidence?.is_verified ? '✓ VERIFIED AGAINST SOURCE' : '⚠ UNVERIFIED / NO MATCH'}
                  </span>
                </div>
                <button
                  onClick={() => setActiveEvidenceModal(null)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-lg"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};
