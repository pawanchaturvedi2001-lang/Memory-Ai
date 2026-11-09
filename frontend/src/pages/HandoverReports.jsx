import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Layout } from '../components/Layout';
import api from '../api/client';
import {
  FileText,
  Download,
  CheckCircle2,
  AlertTriangle,
  FolderKanban,
  BrainCircuit,
  ShieldCheck,
  ListTodo,
  AlertOctagon,
  Printer
} from 'lucide-react';

export const HandoverReports = () => {
  const [searchParams] = useSearchParams();
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(searchParams.get('project_id') || '');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState('');

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

  const fetchReport = async () => {
    if (!selectedProjectId) return;
    try {
      setLoading(true);
      const res = await api.get(`/reports/${selectedProjectId}`);
      setReportData(res.data);
    } catch (err) {
      setError('Failed to generate report summary: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [selectedProjectId]);

  const handleDownloadPdf = async () => {
    if (!selectedProjectId) return;
    try {
      setDownloading(true);
      const response = await api.get(`/reports/${selectedProjectId}/download`, {
        responseType: 'blob'
      });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Handover_Report_Project_${selectedProjectId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to download PDF report: ' + (err.response?.data?.detail || err.message));
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Layout title="Executive Handover & Continuity Report">
      {/* Top Controls */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 mb-6 shadow-2xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
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
        </div>

        <button
          onClick={handleDownloadPdf}
          disabled={downloading || !selectedProjectId}
          className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-colors flex items-center gap-2 shadow-sm disabled:opacity-50"
        >
          <Download className={`w-4 h-4 ${downloading ? 'animate-bounce' : ''}`} />
          {downloading ? 'Compiling PDF via ReportLab...' : 'Download Official PDF Handover Report'}
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : !reportData ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500 text-xs">
          No report data available for this project.
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-2xs max-w-4xl mx-auto space-y-8">
          {/* Document Header */}
          <div className="border-b border-slate-200 pb-6 flex items-start justify-between">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                ReportLab Grounded Handover Document
              </span>
              <h2 className="text-2xl font-black text-slate-900 mt-2 tracking-tight">
                {reportData.project.name}
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                Generated: {new Date().toLocaleString()} &bull; Status: {reportData.project.status}
              </p>
            </div>
            <div className="text-right">
              <span className="text-xs font-bold text-slate-400">PROJECT ID</span>
              <p className="text-lg font-black text-slate-800">#{reportData.project.id}</p>
            </div>
          </div>

          {/* Section 1: Project Overview */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-blue-700 mb-2">
              1. Project Overview & System Context
            </h3>
            <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100">
              {reportData.project.description || 'No formal overview recorded.'}
            </p>
          </div>

          {/* Section 2: Technology Stack */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-blue-700 mb-2">
              2. Technology Stack & Frameworks
            </h3>
            {reportData.sections.tech_stack?.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {reportData.sections.tech_stack.map((t) => (
                  <div key={t.id} className="p-3 rounded-xl border border-slate-200 bg-slate-50/50">
                    <strong className="text-xs text-slate-900 block">{t.title}</strong>
                    <span className="text-[11px] text-slate-600 mt-0.5 block">{t.content}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No specific tech stack items extracted.</p>
            )}
          </div>

          {/* Section 3: Technical Decisions */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-blue-700 mb-2">
              3. Technical Decisions & ADRs
            </h3>
            {reportData.sections.technical_decisions?.length > 0 ? (
              <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
                {reportData.sections.technical_decisions.map((d) => (
                  <div key={d.id} className="p-3.5 bg-white text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <strong className="text-slate-900">{d.title}</strong>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700">
                        {d.status}
                      </span>
                    </div>
                    <p className="text-slate-600">{d.content}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No technical decisions documented.</p>
            )}
          </div>

          {/* Section 4: Pending Tasks & Ownership */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-blue-700 mb-2">
              4. Pending Tasks & Operational Continuity
            </h3>
            {reportData.sections.pending_tasks?.length > 0 ? (
              <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden text-xs">
                {reportData.sections.pending_tasks.map((task) => (
                  <div key={task.id} className="p-3 bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <strong className="text-slate-900">{task.title}</strong>
                      <p className="text-slate-500 text-[11px] mt-0.5">{task.description}</p>
                    </div>
                    <div className="flex items-center gap-3 text-right shrink-0">
                      <div>
                        <span className="text-[10px] text-slate-400 block uppercase">Owner</span>
                        <strong className={task.owner ? 'text-slate-800' : 'text-rose-600'}>
                          {task.owner || 'UNASSIGNED'}
                        </strong>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 block uppercase">Deadline</span>
                        <strong className={task.deadline ? 'text-slate-800' : 'text-amber-600'}>
                          {task.deadline || 'MISSING'}
                        </strong>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No pending tasks recorded.</p>
            )}
          </div>

          {/* Section 5: Unresolved Bugs */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-blue-700 mb-2">
              5. Unresolved Bugs & Critical Incidents
            </h3>
            {reportData.sections.unresolved_bugs?.length > 0 ? (
              <div className="space-y-2">
                {reportData.sections.unresolved_bugs.map((b) => (
                  <div key={b.id} className="p-3.5 rounded-xl bg-red-50/70 border border-red-200 text-xs">
                    <strong className="text-red-900 block font-bold">{b.title}</strong>
                    <p className="text-red-800 mt-1">{b.content}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No active unresolved bugs.</p>
            )}
          </div>

          {/* Section 6 & 7: Dependencies & Risks */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-blue-700 mb-2">
              6. External Dependencies & Project Risks
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              {reportData.sections.dependencies?.map((dep) => (
                <div key={dep.id} className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                  <span className="text-[10px] font-bold text-indigo-600 uppercase block">Dependency</span>
                  <strong className="text-slate-900 block mt-0.5">{dep.title}</strong>
                  <p className="text-slate-600 text-[11px] mt-1">{dep.content}</p>
                </div>
              ))}
              {reportData.sections.risks?.map((risk) => (
                <div key={risk.id} className="p-3 rounded-xl border border-amber-200 bg-amber-50/50">
                  <span className="text-[10px] font-bold text-amber-700 uppercase block">Risk Alert</span>
                  <strong className="text-slate-900 block mt-0.5">{risk.title}</strong>
                  <p className="text-amber-900 text-[11px] mt-1">{risk.content}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Section 8: Knowledge Gaps (Innovation) */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-rose-700 mb-2">
              7. Knowledge Gaps & Inconsistencies Audited
            </h3>
            {reportData.sections.knowledge_gaps?.length > 0 ? (
              <div className="space-y-2">
                {reportData.sections.knowledge_gaps.map((g) => (
                  <div key={g.id} className="p-3 rounded-xl border border-rose-200 bg-rose-50/40 text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <strong className="text-rose-900">{g.title}</strong>
                      <span className="px-2 py-0.5 text-[9px] font-bold rounded bg-rose-200 text-rose-900">
                        {g.severity}
                      </span>
                    </div>
                    <p className="text-slate-700">{g.description}</p>
                    {g.suggested_action && (
                      <p className="text-amber-800 font-medium text-[11px] mt-1">
                        <strong>Action:</strong> {g.suggested_action}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No knowledge gaps detected.</p>
            )}
          </div>
        </div>
      )}
    </Layout>
  );
};
