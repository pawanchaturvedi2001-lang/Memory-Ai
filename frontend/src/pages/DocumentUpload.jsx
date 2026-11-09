import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import api from '../api/client';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, X, BrainCircuit, Sparkles } from 'lucide-react';

export const DocumentUpload = () => {
  const [searchParams] = useSearchParams();
  const initialProjectId = searchParams.get('project_id') || '';
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState(initialProjectId);
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // 'success' | 'error' | null
  const [statusMessage, setStatusMessage] = useState('');
  const [recentUpload, setRecentUpload] = useState(null);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const res = await api.get('/projects');
        setProjects(res.data);
        if (!projectId && res.data.length > 0) {
          setProjectId(res.data[0].id.toString());
        }
      } catch (err) {
        console.error('Failed to fetch projects', err);
      }
    };
    fetchProjects();
  }, []);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    setUploadStatus(null);
    setStatusMessage('');

    if (!selectedFile) return;

    const allowed = ['.pdf', '.docx', '.txt'];
    const ext = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase();

    if (!allowed.includes(ext)) {
      setUploadStatus('error');
      setStatusMessage(`Invalid file format '${ext}'. Only PDF, DOCX, and TXT files are supported.`);
      return;
    }

    if (selectedFile.size > 30 * 1024 * 1024) {
      setUploadStatus('error');
      setStatusMessage('File size exceeds the 30MB limit.');
      return;
    }

    setFile(selectedFile);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file || !projectId) {
      alert('Please select a target project and a document file.');
      return;
    }

    const formData = new FormData();
    formData.append('project_id', projectId);
    formData.append('file', file);
    formData.append('auto_extract', 'true');

    try {
      setUploading(true);
      setUploadStatus(null);
      setStatusMessage('');

      const res = await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setUploadStatus('success');
      setStatusMessage(`Successfully processed '${res.data.filename}'. AI extracted knowledge and updated continuity gaps.`);
      setRecentUpload(res.data);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      setUploadStatus('error');
      setStatusMessage('Upload failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUploading(false);
    }
  };

  return (
    <Layout title="Document Ingestion & Text Processing">
      <div className="max-w-3xl mx-auto">
        <div className="mb-6">
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">Project Document Ingestion</h2>
          <p className="text-xs text-slate-500">
            Upload architecture specs, ADRs, meeting notes, or bug logs. Our AI automatically parses, extracts structured knowledge items, and verifies evidence citations.
          </p>
        </div>

        {uploadStatus === 'success' && (
          <div className="mb-6 p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-bold text-sm">Processing Complete</p>
              <p className="mt-0.5">{statusMessage}</p>
              <div className="flex items-center gap-3 mt-3">
                <button
                  onClick={() => navigate(`/knowledge?project_id=${projectId}`)}
                  className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white font-bold text-xs hover:bg-emerald-700 transition-colors shadow-2xs"
                >
                  View Extracted Knowledge Base
                </button>
                <button
                  onClick={() => navigate(`/gaps?project_id=${projectId}`)}
                  className="px-3 py-1.5 rounded-lg bg-white text-emerald-800 border border-emerald-300 font-bold text-xs hover:bg-emerald-100 transition-colors"
                >
                  Inspect Gaps
                </button>
              </div>
            </div>
          </div>
        )}

        {uploadStatus === 'error' && (
          <div className="mb-6 p-4 rounded-2xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-sm">Upload Error</p>
              <p className="mt-0.5">{statusMessage}</p>
            </div>
          </div>
        )}

        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-2xs">
          <form onSubmit={handleUpload} className="space-y-6">
            {/* Project Picker */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Target Handover Project
              </label>
              <select
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                required
                className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white font-medium"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} (#{p.id})
                  </option>
                ))}
              </select>
            </div>

            {/* Drag & Drop Upload Zone */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Upload File (PDF, DOCX, TXT)
              </label>
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
                  dragActive
                    ? 'border-blue-500 bg-blue-50/50 scale-[1.01]'
                    : file
                    ? 'border-emerald-400 bg-emerald-50/20'
                    : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/50'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleChange}
                  className="hidden"
                />

                {file ? (
                  <div className="flex flex-col items-center">
                    <div className="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-600 flex items-center justify-center mb-3">
                      <FileText className="w-6 h-6" />
                    </div>
                    <p className="text-sm font-bold text-slate-900">{file.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {(file.size / 1024).toFixed(1)} KB &bull; Ready for AI extraction
                    </p>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setFile(null);
                      }}
                      className="mt-3 text-xs font-bold text-rose-600 hover:text-rose-700 flex items-center gap-1"
                    >
                      <X className="w-3.5 h-3.5" /> Remove file
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
                      <UploadCloud className="w-6 h-6" />
                    </div>
                    <p className="text-sm font-bold text-slate-900">
                      Click to upload or drag & drop documents here
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
                      Supports PDF, DOCX, TXT up to 30MB
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* AI Ingestion Options */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <BrainCircuit className="w-4 h-4 text-blue-600 shrink-0" />
                <div>
                  <p className="text-xs font-bold text-slate-900">Evidence Grounding & Knowledge Synthesis</p>
                  <p className="text-[11px] text-slate-500">Extracts technical decisions, tasks, bugs, risks, and maps verbatim excerpts.</p>
                </div>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-100 text-blue-700">
                Enabled
              </span>
            </div>

            <button
              type="submit"
              disabled={!file || uploading}
              className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-bold transition-colors flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
            >
              {uploading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Parsing & Synthesizing Knowledge...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Process & Ingest Document
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </Layout>
  );
};
