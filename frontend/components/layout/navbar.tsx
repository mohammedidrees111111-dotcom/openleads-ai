"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Bell,
  LogOut,
  Moon,
  Sun,
  User,
  Settings,
  Mail,
  Users,
  Zap,
} from "lucide-react";
import { useState, useRef, useEffect } from "react";

export function Navbar() {
  const router = useRouter();
  const [darkMode, setDarkMode] = useState(true);
  const [showNotifications, setShowNotifications] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!showNotifications) return;
    const handleClick = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifications(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [showNotifications]);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle("dark");
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    router.push("/login");
  };

  const notifications = [
    { icon: Mail, text: "5 new emails opened", time: "2m ago", color: "text-blue-500" },
    { icon: Users, text: "3 new leads found", time: "15m ago", color: "text-green-500" },
    { icon: Zap, text: "AI scoring completed", time: "1h ago", color: "text-purple-500" },
  ];

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6">
      <div className="flex-1" />

      <button
        onClick={toggleDarkMode}
        className="rounded-lg p-2 hover:bg-accent transition-colors"
      >
        {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
      </button>

      <div className="relative" ref={notifRef}>
        <button
          onClick={() => setShowNotifications(!showNotifications)}
          className="relative rounded-lg p-2 hover:bg-accent transition-colors"
        >
          <Bell className="h-5 w-5" />
          <span className="absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-medium text-primary-foreground">
            {notifications.length}
          </span>
        </button>
        {showNotifications && (
          <div className="absolute right-0 top-full mt-2 w-72 rounded-lg border bg-card shadow-lg z-50">
            <div className="p-3 border-b"><p className="text-sm font-medium">Notifications</p></div>
            <div className="p-2 space-y-1">
              {notifications.map((n, i) => (
                <div key={i} className="flex items-center gap-3 p-2 rounded-lg hover:bg-accent transition-colors cursor-pointer">
                  <n.icon className={`h-4 w-4 ${n.color}`} />
                  <div className="flex-1">
                    <p className="text-sm">{n.text}</p>
                    <p className="text-xs text-muted-foreground">{n.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-primary to-purple-600 text-sm font-bold text-white">
          MI
        </div>
        <div className="hidden md:block">
          <p className="text-sm font-medium">Mohammed Idrees</p>
          <p className="text-xs text-muted-foreground">Agency Owner</p>
        </div>
      </div>

      <Button variant="ghost" size="icon" onClick={handleLogout}>
        <LogOut className="h-4 w-4" />
      </Button>
    </header>
  );
}
