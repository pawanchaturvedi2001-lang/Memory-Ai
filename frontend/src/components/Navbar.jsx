import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, Sparkles, Shield, UserCircle, RefreshCw } from 'lucide-react';
import api from '../api/client';

export const Navbar = ({ title }) => {
  const { user, logout, setUser } = useAuth();
  const [seeding, setSeeding] = useState(false);
  const [switching, setSwitching] = useState(false);

  const handleSeedDemo = async () => {
    try {
      setSeeding(true);
      await api.post('/demo/seed');
      window.location.reload();
    } catch (err) {
      alert('Failed to seed demo data: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSeeding(false);
    }
  };

  const handleRoleSwitch = async (newRole) => {
    if (!user) return;
    try {
      setSwitching(true);
      const res = await api.patch(`/auth/users/${user.id}/role`, { role: newRole });
      setUser(res.data);
      localStorage.setItem('memory_ai_user', JSON.stringify(res.data));
    } catch (err) {
      alert('Role switch failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSwitching(false);
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-10">
      <div>
        <h1 className="text-lg font-bold text-slate-900 tracking-tight">{title || 'Dashboard'}</h1>
      </div>

      <div className="flex items-center gap-3">
        {/* Hackathon Demo Quick Seed Button */}
        <button
          onClick={handleSeedDemo}
          disabled={seeding}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors border border-indigo-200 shadow-2xs"
          title="Seeds or resets synthetic E-Commerce demo dataset with 5 intentional anomalies"
        >
          <Sparkles className={`w-3.5 h-3.5 text-indigo-600 ${seeding ? 'animate-spin' : ''}`} />
          {seeding ? 'Seeding Demo...' : 'Reset Demo Dataset'}
        </button>

        {/* Role Quick Switcher for Demo Testing */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200">
          <span className="text-[11px] font-medium text-slate-500 px-1.5">Role:</span>
          <select
            value={user?.role || 'Incoming Member'}
            onChange={(e) => handleRoleSwitch(e.target.value)}
            disabled={switching}
            className="text-xs font-semibold bg-white text-slate-800 border-none rounded py-1 px-2 focus:ring-1 focus:ring-blue-500 cursor-pointer shadow-2xs"
          >
            <option value="Admin">Admin</option>
            <option value="Manager">Manager</option>
            <option value="Outgoing Member">Outgoing Member</option>
            <option value="Incoming Member">Incoming Member</option>
          </select>
        </div>

        {/* User profile dropdown / logout */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
          <button
            onClick={logout}
            className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
