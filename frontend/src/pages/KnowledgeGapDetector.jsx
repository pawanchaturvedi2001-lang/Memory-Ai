import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Layout } from '../components/Layout';
import api from '../api/client';
import {
  SearchCode,
  ShieldAlert,
  AlertTriangle,
  RefreshCw,
  AlertCircle,
  HelpCircle,
  ArrowRight,
  CheckCircle,
  Zap,
  Filter
} from 'lucide-react';
import { SeverityBadge } from '../components/StatusBadge';

export const KnowledgeGapDetector = () => {
  const [searchParams] = useSearchParams();
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(searchParams.get('project_id') || '');
  const [gaps, setGaps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('ALL');

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

  const fetchGaps = async () => {
    if (!selectedProjectId) return;
    try {
      setLoading(true);
      const res = await api.get(`/knowledge/${selectedProjectId}/gaps`);
      setGaps(res.data);
    } catch (err) {
      setError('Failed to fetch knowledge gaps: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGaps();
  }, [selectedProjectId]);

  const handleRunAnalysis = async () => {
    if (!selectedProjectId) return;
    try {
      setAnalyzing(true);
      const res = await api.post(`/knowledge/${selectedProjectId}/analyze-gaps`);
      setGaps(res.data);
    } catch (err) {
      alert('Analysis failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setAnalyzing(false);
    }
  };

  const filteredGaps = gaps.filter((g) => {
    if (filterSeverity === 'ALL') return true;
    return g.severity === filterSeverity;
  });

  return (
    <Layout title="Knowledge Gap Detector & Consistency Auditor">
      {/* Top Banner Explaining Main Innovation */}
      <div className="mb-6 p-6 rounded-2xl bg-gradient-to-r from-rose-950 via-slate-900 to-indigo-950 text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-rose-500 text-white shadow-2xs">
              Primary Innovation
            </span>
            <span className="text-xs text-rose-300 font-medium">Deterministic Rule-Based Inconsistency Engine</span>
          </div>
          <h2 className="text-2xl font-black tracking-tight">Autonomous Knowledge Gap Auditing</h2>
          <p className="text-slate-300 text-xs max-w-2xl mt-1">
            Uncovers missing task ownership, conflicting deadlines, unverified architectural choices, active unresolved bugs, and unconfigured dependencies before they cause outages.
          </p>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={analyzing || !selectedProjectId}
          className="px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold transition-colors flex items-center gap-2 shadow-sm shrink-0 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${analyzing ? 'animate-spin' : ''}`} />
          {analyzing ? 'Auditing Documentation...' : 'Re-Run Gap Analysis'}
        </button>
      </div>

      {/* Filter and Project Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 mb-6 shadow-2xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1 min-w-[280px]">
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="text-xs font-semibold px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-blue-500"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                Project: {p.name}
              </option>
            ))}
          </select>

          <span className="text-xs text-slate-500 font-medium">
            Found <strong className="text-rose-600">{gaps.length}</strong> gaps in current project
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Severity:</span>
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="text-xs font-medium px-3 py-2 rounded-xl border border-slate-200 bg-white"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="w-8 h-8 border-3 border-rose-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : filteredGaps.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
          <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-900">Zero Open Knowledge Gaps Detected</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
            All documented tasks have valid owners and non-conflicting deadlines, and all architecture decisions are verified against source evidence.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredGaps.map((gap) => (
            <div
              key={gap.id}
              className="bg-white rounded-2xl border border-slate-200 p-5 shadow-2xs hover:border-rose-300 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2.5">
                  <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-rose-50 text-rose-700 border border-rose-200">
                    {gap.gap_type.replace('_', ' ')}
                  </span>
                  <SeverityBadge severity={gap.severity} />
                </div>

                <h3 className="text-sm font-bold text-slate-900 mb-1.5">{gap.title}</h3>
                <p className="text-xs text-slate-600 leading-relaxed">{gap.description}</p>
              </div>

              {gap.suggested_action && (
                <div className="mt-4 p-3 rounded-xl bg-amber-50/70 border border-amber-200/70">
                  <div className="flex items-center gap-1.5 text-amber-800 text-[11px] font-bold mb-0.5">
                    <Zap className="w-3.5 h-3.5 text-amber-600" />
                    Recommended Continuity Action:
                  </div>
                  <p className="text-xs text-amber-900">{gap.suggested_action}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
};
