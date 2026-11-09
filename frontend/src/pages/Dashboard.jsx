import React, { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import api from '../api/client';
import {
  FolderKanban,
  FileText,
  BrainCircuit,
  ListTodo,
  AlertOctagon,
  SearchCode,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  TrendingUp,
  Activity,
  ShieldAlert,
  Download
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { StatusBadge, SeverityBadge } from '../components/StatusBadge';

export const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        const res = await api.get('/dashboard/stats');
        setStats(res.data);
      } catch (err) {
        setError('Failed to load dashboard metrics: ' + (err.response?.data?.detail || err.message));
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <Layout title="Executive Overview">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            <p className="text-xs font-semibold text-slate-500">Loading live telemetry and handover metrics...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Dashboard & Continuity Telemetry">
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm font-medium">
          {error}
        </div>
      )}

      {/* Top Highlight Banner */}
      <div className="mb-8 p-6 rounded-2xl bg-gradient-to-r from-blue-900 via-blue-800 to-indigo-900 text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-500/30 text-blue-200 border border-blue-400/30 mb-2 inline-block">
            Autonomous Continuity Engine
          </span>
          <h2 className="text-2xl font-extrabold tracking-tight">Active Handover Intelligence</h2>
          <p className="text-blue-200 text-sm max-w-2xl mt-1">
            Real-time project knowledge synthesis, automated gap auditing, and source-grounded continuity assurance.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/gaps"
            className="px-4 py-2.5 rounded-xl bg-rose-500 hover:bg-rose-600 text-white text-xs font-bold transition-colors flex items-center gap-2 shadow-sm"
          >
            <ShieldAlert className="w-4 h-4" />
            Inspect {stats?.knowledge_gaps || 0} Knowledge Gaps
          </Link>
          <Link
            to="/reports"
            className="px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-bold transition-colors flex items-center gap-2 border border-white/20"
          >
            <Download className="w-4 h-4" />
            Export Reports
          </Link>
        </div>
      </div>

      {/* 7 Core Required Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {/* Total Projects */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Projects</span>
            <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <FolderKanban className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-slate-900">{stats?.total_projects || 0}</div>
          <div className="mt-2 text-[11px] text-slate-500 flex items-center gap-1 font-medium">
            <span className="text-emerald-600 font-bold">Live DB:</span> Active handover repos
          </div>
        </div>

        {/* Uploaded Documents */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Uploaded Documents</span>
            <div className="w-8 h-8 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-slate-900">{stats?.total_documents || 0}</div>
          <div className="mt-2 text-[11px] text-slate-500 flex items-center gap-1 font-medium">
            <span className="text-blue-600 font-bold">PDF, DOCX, TXT</span> parsed & indexed
          </div>
        </div>

        {/* Extracted Knowledge Items */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Knowledge Items</span>
            <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <BrainCircuit className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-slate-900">{stats?.total_knowledge_items || 0}</div>
          <div className="mt-2 text-[11px] text-slate-500 flex items-center gap-1 font-medium">
            <span className="text-emerald-600 font-bold">100% Traceable</span> to source citations
          </div>
        </div>

        {/* Knowledge Gaps */}
        <div className="bg-white p-5 rounded-2xl border border-rose-200 shadow-2xs hover:border-rose-300 transition-all bg-gradient-to-br from-white to-rose-50/30">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-rose-700 uppercase tracking-wider">Knowledge Gaps</span>
            <div className="w-8 h-8 rounded-xl bg-rose-100 text-rose-600 flex items-center justify-center">
              <SearchCode className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-rose-700">{stats?.knowledge_gaps || 0}</div>
          <div className="mt-2 text-[11px] text-rose-600 font-medium">
            Deterministic rules flagged inconsistencies
          </div>
        </div>
      </div>

      {/* Row 2: Secondary Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {/* Pending Tasks */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500">Pending Tasks</span>
            <ListTodo className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{stats?.pending_tasks || 0}</div>
          <p className="text-xs text-slate-500 mt-1">Pending action items awaiting incoming dev pickup</p>
        </div>

        {/* Unresolved Issues */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500">Unresolved Issues</span>
            <AlertOctagon className="w-4 h-4 text-red-500" />
          </div>
          <div className="text-2xl font-bold text-red-600">{stats?.unresolved_issues || 0}</div>
          <p className="text-xs text-slate-500 mt-1">Active production bugs reported in documentation</p>
        </div>

        {/* Approvals Overview */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500">Approval Workflow</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="flex items-baseline gap-3">
            <span className="text-2xl font-bold text-emerald-600">{stats?.approved_items || 0} <span className="text-xs font-normal text-slate-400">Approved</span></span>
            <span className="text-sm font-semibold text-amber-600">{stats?.needs_review_items || 0} <span className="text-xs font-normal text-slate-400">Review</span></span>
          </div>
          <p className="text-xs text-slate-500 mt-1">Human governance verifying AI extractions</p>
        </div>
      </div>

      {/* Real Audit History Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-bold text-slate-900">Live Audit Trail & Handover Log</h3>
          </div>
          <span className="text-xs text-slate-400 font-medium">Real-time system events</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/75 border-b border-slate-100 text-slate-500 uppercase font-semibold">
              <tr>
                <th className="px-6 py-3">Timestamp</th>
                <th className="px-6 py-3">Action</th>
                <th className="px-6 py-3">Entity</th>
                <th className="px-6 py-3">User / Initiator</th>
                <th className="px-6 py-3">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {stats?.recent_activity?.length > 0 ? (
                stats.recent_activity.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-3 text-slate-500 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-3 font-semibold text-slate-900">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-100 text-slate-800">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-slate-600 capitalize">
                      {log.entity_type}
                    </td>
                    <td className="px-6 py-3 text-slate-600">
                      {log.user?.email || 'System Agent'}
                    </td>
                    <td className="px-6 py-3 text-slate-700 max-w-md truncate">
                      {log.details || '—'}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400">
                    No activity logs recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
};
