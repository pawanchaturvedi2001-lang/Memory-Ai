import React, { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import api from '../api/client';
import { Users, Shield, UserCheck, ShieldAlert, CheckCircle2, Clock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [updatingId, setUpdatingId] = useState(null);
  const { user: currentUser } = useAuth();

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const res = await api.get('/auth/users');
      setUsers(res.data);
    } catch (err) {
      setError('Failed to load user directory: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleRoleChange = async (userId, newRole) => {
    try {
      setUpdatingId(userId);
      await api.patch(`/auth/users/${userId}/role`, { role: newRole });
      fetchUsers();
    } catch (err) {
      alert('Role update failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <Layout title="User & Role Governance">
      <div className="mb-6">
        <h2 className="text-lg font-bold text-slate-900 tracking-tight">Workspace Users & Role Permissions</h2>
        <p className="text-xs text-slate-500">
          Control access levels. Outgoing leads review extractions; Incoming devs access authorized continuity knowledge.
        </p>
      </div>

      {/* Role Definitions Guide Card */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <div className="p-3.5 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-xs font-bold text-blue-700 block mb-1">Admin</span>
          <p className="text-[11px] text-slate-500">Full platform governance, all projects, member management, and role assignment.</p>
        </div>
        <div className="p-3.5 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-xs font-bold text-amber-700 block mb-1">Manager</span>
          <p className="text-[11px] text-slate-500">Project creation, document approval sign-offs, and team assignment oversight.</p>
        </div>
        <div className="p-3.5 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-xs font-bold text-indigo-700 block mb-1">Outgoing Member</span>
          <p className="text-[11px] text-slate-500">Departing architect/lead uploading knowledge, editing claims, and resolving gaps.</p>
        </div>
        <div className="p-3.5 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-xs font-bold text-emerald-700 block mb-1">Incoming Member</span>
          <p className="text-[11px] text-slate-500">New team member onboarding. Accesses verified, approved handover items & tasks.</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-2xs overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/75 border-b border-slate-100 text-slate-500 uppercase font-semibold">
              <tr>
                <th className="px-6 py-3.5">User</th>
                <th className="px-6 py-3.5">Email</th>
                <th className="px-6 py-3.5">Assigned Role</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Joined Date</th>
                <th className="px-6 py-3.5 text-right">Modify Role</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50/50 transition-colors">
                  <td className="px-6 py-3.5 font-bold text-slate-900 flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-xs">
                      {u.full_name ? u.full_name[0].toUpperCase() : 'U'}
                    </div>
                    <span>{u.full_name}</span>
                  </td>
                  <td className="px-6 py-3.5 text-slate-600 font-mono text-[11px]">{u.email}</td>
                  <td className="px-6 py-3.5">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                      {u.role}
                    </span>
                  </td>
                  <td className="px-6 py-3.5">
                    <span className="flex items-center gap-1 text-emerald-700 font-medium text-[11px]">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      Active
                    </span>
                  </td>
                  <td className="px-6 py-3.5 text-slate-500 text-[11px]">
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-3.5 text-right">
                    <select
                      value={u.role}
                      disabled={updatingId === u.id || (currentUser?.role !== 'Admin' && currentUser?.role !== 'Manager')}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                      className="text-xs font-semibold px-2 py-1 border border-slate-200 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 cursor-pointer disabled:opacity-50"
                    >
                      <option value="Admin">Admin</option>
                      <option value="Manager">Manager</option>
                      <option value="Outgoing Member">Outgoing Member</option>
                      <option value="Incoming Member">Incoming Member</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Layout>
  );
};
