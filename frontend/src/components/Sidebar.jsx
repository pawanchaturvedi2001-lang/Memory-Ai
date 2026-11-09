import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderKanban,
  UploadCloud,
  BrainCircuit,
  SearchCode,
  CheckSquare,
  FileText,
  Users,
  Sparkles,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Sidebar = () => {
  const { user } = useAuth();

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Projects', path: '/projects', icon: FolderKanban },
    { label: 'Document Upload', path: '/upload', icon: UploadCloud },
    { label: 'Knowledge Base', path: '/knowledge', icon: BrainCircuit },
    { label: 'Knowledge Gap Detector', path: '/gaps', icon: SearchCode, highlight: true },
    { label: 'Approval Workflow', path: '/approvals', icon: CheckSquare },
    { label: 'Handover Reports', path: '/reports', icon: FileText },
    { label: 'Users & Roles', path: '/users', icon: Users, adminOnly: true },
  ];

  const filteredItems = navItems.filter(item => {
    if (item.adminOnly && user?.role !== 'Admin' && user?.role !== 'Manager') {
      return false;
    }
    return true;
  });

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0 h-screen sticky top-0">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-100 gap-3">
        <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
          <BrainCircuit className="w-5 h-5" />
        </div>
        <div>
          <span className="font-bold text-slate-900 tracking-tight text-base flex items-center gap-1.5">
            MEMORY <span className="text-blue-600 font-extrabold">AI</span>
          </span>
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider block">
            Team Continuity
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Core Platform
        </div>
        {filteredItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 font-semibold shadow-xs'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                } ${item.highlight ? 'border border-blue-100' : ''}`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${item.highlight ? 'text-blue-600' : ''}`} />
                <span>{item.label}</span>
              </div>
              {item.highlight && (
                <span className="px-1.5 py-0.5 text-[9px] font-bold uppercase rounded bg-blue-600 text-white">
                  Core
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Role / Current User Badge */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-xs">
            {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-slate-900 truncate">{user?.full_name || 'Guest User'}</p>
            <p className="text-[11px] text-blue-600 font-medium truncate">{user?.role || 'Incoming Member'}</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
