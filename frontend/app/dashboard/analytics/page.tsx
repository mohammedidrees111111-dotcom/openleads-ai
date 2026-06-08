"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { analyticsAPI } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";
import {
  BarChart3, TrendingUp, DollarSign, Target, PieChart,
  ArrowUp, ArrowDown, Activity,
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart as RePieChart, Pie, Cell, LineChart, Line, CartesianGrid, Legend } from "recharts";

const COLORS = ["#6366f1", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444"];

export default function AnalyticsPage() {
  const [stats, setStats] = useState<any>(null);
  const [daily, setDaily] = useState<any[]>([]);
  const [channels, setChannels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      setError("");
      const [statsRes, dailyRes, channelsRes] = await Promise.all([
        analyticsAPI.dashboard(),
        analyticsAPI.daily(30),
        analyticsAPI.channels(),
      ]);
      setStats(statsRes.data);
      setDaily(dailyRes.data.map((d: any) => ({ ...d, date: d.date?.slice(5) })));
      setChannels(channelsRes.data);
    } catch (err) { setError("Failed to load analytics data"); }
    finally { setLoading(false); }
  };

  if (error) {
    return <div className="flex items-center justify-center h-96"><div className="text-center"><p className="text-red-400 mb-2">{error}</p><Button variant="outline" onClick={loadData}>Retry</Button></div></div>;
  }

  if (loading) {
    return <div className="flex items-center justify-center h-96"><div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div>;
  }

  const chartData = daily.length > 0 ? daily : [];
  const channelData = (channels || []).map((c: any) => ({ name: c.channel, value: c.sent || 0 }));

  return (
    <div className="space-y-6 animate-fade-in">
      <div><h1 className="text-3xl font-bold">Analytics</h1><p className="text-muted-foreground">Detailed performance metrics and insights</p></div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Open Rate", value: formatPercent(stats?.open_rate || 0), icon: Activity, color: "text-blue-500", change: "+2.3%" },
          { label: "Reply Rate", value: formatPercent(stats?.reply_rate || 0), icon: Target, color: "text-green-500", change: "+1.8%" },
          { label: "Conversion Rate", value: formatPercent(stats?.conversion_rate || 0), icon: TrendingUp, color: "text-purple-500", change: "+0.5%" },
          { label: "Bounce Rate", value: formatPercent(stats?.bounce_rate || 0), icon: BarChart3, color: "text-red-500", change: "-0.3%" },
        ].map((metric, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">{metric.label}</span>
                <metric.icon className={`h-5 w-5 ${metric.color}`} />
              </div>
              <p className="text-3xl font-bold">{metric.value}</p>
              <div className="flex items-center gap-1 mt-2">
                {metric.change.startsWith("+") ? <ArrowUp className="h-3 w-3 text-green-500" /> : <ArrowDown className="h-3 w-3 text-red-500" />}
                <span className={`text-xs ${metric.change.startsWith("+") ? "text-green-500" : "text-red-500"}`}>{metric.change} vs last month</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle className="flex items-center gap-2"><BarChart3 className="h-5 w-5 text-primary" /> 30-Day Performance</CardTitle></CardHeader>
          <CardContent className="h-80">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
                  <YAxis tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
                  <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} />
                  <Legend />
                  <Line type="monotone" dataKey="emails_sent" stroke="#6366f1" strokeWidth={2} dot={false} name="Sent" />
                  <Line type="monotone" dataKey="emails_opened" stroke="#10b981" strokeWidth={2} dot={false} name="Opened" />
                  <Line type="monotone" dataKey="emails_replied" stroke="#f59e0b" strokeWidth={2} dot={false} name="Replied" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground">No daily data yet. Start sending emails to see trends.</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><PieChart className="h-5 w-5 text-primary" /> Channel Distribution</CardTitle></CardHeader>
          <CardContent className="h-64">
            {channelData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <RePieChart>
                  <Pie data={channelData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                    {channelData.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                </RePieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground">No channel data yet</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><DollarSign className="h-5 w-5 text-primary" /> MRR Growth</CardTitle></CardHeader>
          <CardContent>
            <div className="text-center mb-6">
              <p className="text-4xl font-bold gradient-text">{formatCurrency(stats?.current_mrr || 0)}</p>
              <p className="text-sm text-muted-foreground">Current MRR</p>
            </div>
            <div className="space-y-3">
              <div className="p-3 rounded-lg bg-secondary/50"><div className="flex justify-between mb-1"><span className="text-sm">Target MRR</span><span className="text-sm font-bold">$2,999</span></div><div className="h-2 rounded-full bg-secondary overflow-hidden"><div className="h-full rounded-full bg-gradient-to-r from-primary to-purple-500 transition-all" style={{ width: `${Math.min(100, ((stats?.current_mrr || 0) / 2999) * 100)}%` }} /></div></div>
              {[{ label: "Starter", price: "$299/mo" }, { label: "Growth", price: "$599/mo" }, { label: "Pro", price: "$1,199/mo" }].map((item, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50"><span className="text-sm">{item.label}</span><span className="text-sm font-bold">{item.price}</span></div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Target className="h-5 w-5 text-primary" /> Goal Tracking</CardTitle></CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { label: "Monthly Leads", current: stats?.total_leads || 0, target: 500 },
              { label: "Monthly Revenue", current: stats?.current_mrr || 0, target: 2999, isCurrency: true },
              { label: "Active Campaigns", current: stats?.active_campaigns || 0, target: 10 },
            ].map((goal, i) => (
              <div key={i}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">{goal.label}</span>
                  <span className="text-sm text-muted-foreground">{goal.isCurrency ? formatCurrency(goal.current) : goal.current} / {goal.isCurrency ? formatCurrency(goal.target) : goal.target}</span>
                </div>
                <div className="h-3 rounded-full bg-secondary overflow-hidden">
                  <div className="h-full rounded-full bg-gradient-to-r from-primary to-purple-500 transition-all" style={{ width: `${Math.min(100, (goal.current / goal.target) * 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
