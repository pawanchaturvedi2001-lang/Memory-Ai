import React from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, XCircle, Clock, ShieldCheck, HelpCircle } from 'lucide-react';

export const StatusBadge = ({ status }) => {
  const norm = (status || '').toUpperCase().trim();

  switch (norm) {
    case 'APPROVED':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          APPROVED
        </span>
      );
    case 'SUPPORTED':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
          <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
          SUPPORTED
        </span>
      );
    case 'CONFLICTING':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200 animate-pulse">
          <AlertTriangle className="w-3.5 h-3.5 text-purple-600" />
          CONFLICTING
        </span>
      );
    case 'MISSING EVIDENCE':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
          <HelpCircle className="w-3.5 h-3.5 text-rose-600" />
          MISSING EVIDENCE
        </span>
      );
    case 'UNRESOLVED':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
          <AlertCircle className="w-3.5 h-3.5 text-red-600" />
          UNRESOLVED
        </span>
      );
    case 'NEEDS REVIEW':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
          <Clock className="w-3.5 h-3.5 text-amber-600" />
          NEEDS REVIEW
        </span>
      );
    case 'REJECTED':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-300">
          <XCircle className="w-3.5 h-3.5 text-slate-500" />
          REJECTED
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
          {norm || 'DRAFT'}
        </span>
      );
  }
};

export const SeverityBadge = ({ severity }) => {
  const norm = (severity || '').toUpperCase().trim();
  switch (norm) {
    case 'CRITICAL':
      return <span className="px-2 py-0.5 text-xs font-bold rounded bg-red-100 text-red-800 border border-red-300">CRITICAL</span>;
    case 'HIGH':
      return <span className="px-2 py-0.5 text-xs font-bold rounded bg-orange-100 text-orange-800 border border-orange-300">HIGH</span>;
    case 'MEDIUM':
      return <span className="px-2 py-0.5 text-xs font-medium rounded bg-amber-100 text-amber-800 border border-amber-300">MEDIUM</span>;
    default:
      return <span className="px-2 py-0.5 text-xs font-medium rounded bg-slate-100 text-slate-700 border border-slate-200">LOW</span>;
  }
};
