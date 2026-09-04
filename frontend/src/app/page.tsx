"use client";

import { useState } from "react";
import LoginScreen from "@/components/LoginScreen";
import ChatInterface from "@/components/ChatInterface";
import { LoginResponse } from "@/lib/api";

export default function Home() {
  const [user, setUser] = useState<LoginResponse | null>(null);

  const handleLogin = (data: LoginResponse) => {
    setUser(data);
  };

  const handleLogout = () => {
    setUser(null);
  };

  if (!user) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return <ChatInterface user={user} onLogout={handleLogout} />;
}
