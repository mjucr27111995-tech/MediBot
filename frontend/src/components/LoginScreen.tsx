"use client";

import React, { useState } from "react";
import { login, LoginResponse } from "@/lib/api";

interface DemoUser {
  username: string;
  password: string;
  role: string;
  label: string;
}

const DEMO_USERS: DemoUser[] = [
  { username: "dr.mehta", password: "doctor", role: "doctor", label: "Dr. Anil Mehta" },
  { username: "nurse.priya", password: "nurse", role: "nurse", label: "Priya Sharma" },
  { username: "billing.ravi", password: "billing", role: "billing_executive", label: "Ravi Kumar" },
  { username: "tech.anand", password: "technician", role: "technician", label: "Anand Rao" },
  { username: "admin.sys", password: "admin", role: "admin", label: "System Admin" },
];

const ROLE_COLORS: Record<string, string> = {
  doctor: "bg-blue-100 text-blue-800 border-blue-300",
  nurse: "bg-green-100 text-green-800 border-green-300",
  billing_executive: "bg-purple-100 text-purple-800 border-purple-300",
  technician: "bg-orange-100 text-orange-800 border-orange-300",
  admin: "bg-red-100 text-red-800 border-red-300",
};

const ROLE_ICONS: Record<string, string> = {
  doctor: "🩺",
  nurse: "💉",
  billing_executive: "💰",
  technician: "🔧",
  admin: "🛡️",
};

interface LoginScreenProps {
  onLogin: (data: LoginResponse) => void;
}

export default function LoginScreen({ onLogin }: LoginScreenProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(username, password);
      onLogin(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (user: DemoUser) => {
    setError("");
    setLoading(true);
    try {
      const data = await login(user.username, user.password);
      onLogin(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      <div className="w-full max-w-md mx-4">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-5xl mb-3">🏥</div>
          <h1 className="text-3xl font-bold text-white">MediBot</h1>
          <p className="text-blue-200 mt-2">MediAssist Health Network</p>
          <p className="text-slate-400 text-sm mt-1">
            Intelligent Assistant with Role-Based Access
          </p>
        </div>

        {/* Login Form */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                placeholder="Enter username"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                placeholder="Enter password"
                required
              />
            </div>
            {error && (
              <div className="text-red-600 text-sm bg-red-50 px-3 py-2 rounded-lg">
                {error}
              </div>
            )}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-lg transition disabled:opacity-50"
            >
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>
        </div>

        {/* Quick Login Cards */}
        <div className="bg-white/10 backdrop-blur rounded-2xl p-5">
          <p className="text-blue-200 text-sm font-medium mb-3 text-center">
            Demo Accounts — Quick Login
          </p>
          <div className="grid grid-cols-1 gap-2">
            {DEMO_USERS.map((user) => (
              <button
                key={user.username}
                onClick={() => handleQuickLogin(user)}
                disabled={loading}
                className="flex items-center gap-3 px-4 py-2.5 bg-white/10 hover:bg-white/20 rounded-lg transition text-left disabled:opacity-50"
              >
                <span className="text-xl">{ROLE_ICONS[user.role]}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-white text-sm font-medium">
                    {user.label}
                  </div>
                  <div className="text-blue-300 text-xs">
                    {user.username} / {user.password}
                  </div>
                </div>
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium border ${ROLE_COLORS[user.role]}`}
                >
                  {user.role.replace("_", " ")}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
