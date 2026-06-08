"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Users, Target, Send, TrendingUp, DollarSign, Activity,
  Mail, MessageCircle, Globe, ArrowUp, ArrowDown, Zap,
  BarChart3, PieChart, Map, Sparkles, X, Loader2, Search, Check,
} from "lucide-react";
import { analyticsAPI, clientsAPI, leadsAPI } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent, formatTimeAgo } from "@/lib/utils";

const MODAL_STYLE = "fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm";

const TIER_NAMES: Record<string, string> = {
  free: "Free", starter: "Starter", growth: "Growth", pro: "Pro", enterprise: "Enterprise",
};

const TIER_LIMITS: Record<string, number> = {
  free: 5, starter: 50, growth: 200, pro: 1000, enterprise: 99999,
};

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<any>(null);
  const [pipeline, setPipeline] = useState<any>(null);
  const [activity, setActivity] = useState<any[]>([]);
  const [clients, setClients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // AI Lead Finder state
  const [showFinder, setShowFinder] = useState(false);
  const [finderForm, setFinderForm] = useState({ keywords: "", locations: "", max_leads: 10 });
  const [finderLoading, setFinderLoading] = useState(false);
  const [finderResults, setFinderResults] = useState<any[]>([]);
  const [finderMsg, setFinderMsg] = useState("");
  const [finderTier, setFinderTier] = useState("");
  const [finderRemaining, setFinderRemaining] = useState(0);
  const [finderSaved, setFinderSaved] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setError("");
      const [statsRes, pipelineRes, activityRes, clientsRes] = await Promise.all([
        analyticsAPI.dashboard(),
        analyticsAPI.pipeline(),
        analyticsAPI.activity(10),
        clientsAPI.list({ per_page: 50 }),
      ]);
      setStats(statsRes.data);
      setPipeline(pipelineRes.data);
      setActivity(activityRes.data || []);
      setClients(clientsRes.data.items || []);
    } catch (err) {
      setError("Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  const handleFindLeads = async () => {
    if (!finderForm.keywords) return;
    setFinderLoading(true); setFinderMsg(""); setFinderResults([]); setFinderSaved(false);
    try {
      const res = await leadsAPI.aiFind({
        keywords: finderForm.keywords,
        locations: finderForm.locations,
        max_leads: finderForm.max_leads,
      });
      setFinderResults(res.data.leads || []);
      setFinderTier(res.data.tier);
      setFinderRemaining(res.data.daily_remaining);
      if (res.data.unlimited) {
        setFinderMsg(`Found ${res.data.count} leads! ♾️ Unlimited access — no daily limit.`);
      } else {
        setFinderMsg(`Found ${res.data.count} leads! ${res.data.daily_remaining} remaining today.`);
      }
    } catch (err: any) {
      setFinderMsg(err.response?.data?.detail || "Failed to find leads");
    } finally {
      setFinderLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  const statCards = [
    {
      title: "Total Leads",
      value: formatNumber(stats?.total_leads || 0),
      change: "+12%",
      up: true,
      icon: Users,
      color: "from-blue-500/10 to-blue-600/5 border-blue-500/20",
      iconColor: "text-blue-500",
    },
    {
      title: "Qualified",
      value: formatNumber(stats?.qualified_leads || 0),
      change: `${formatPercent(stats?.qualified_leads / (stats?.total_leads || 1) * 100)}%`,
      up: true,
      icon: Target,
      color: "from-green-500/10 to-green-600/5 border-green-500/20",
      iconColor: "text-green-500",
    },
    {
      title: "Sent",
      value: formatNumber(stats?.total_sent || 0),
      change: "+8%",
      up: true,
      icon: Send,
      color: "from-purple-500/10 to-purple-600/5 border-purple-500/20",
      iconColor: "text-purple-500",
    },
    {
      title: "Open Rate",
      value: formatPercent(stats?.open_rate || 0),
      change: "+3%",
      up: true,
      icon: Activity,
      color: "from-cyan-500/10 to-cyan-600/5 border-cyan-500/20",
      iconColor: "text-cyan-500",
    },
    {
      title: "Reply Rate",
      value: formatPercent(stats?.reply_rate || 0),
      change: "+5%",
      up: true,
      icon: MessageCircle,
      color: "from-orange-500/10 to-orange-600/5 border-orange-500/20",
      iconColor: "text-orange-500",
    },
    {
      title: "Monthly MRR",
      value: formatCurrency(stats?.current_mrr || 0),
      change: "+$299",
      up: true,
      icon: DollarSign,
      color: "from-emerald-500/10 to-emerald-600/5 border-emerald-500/20",
      iconColor: "text-emerald-500",
    },
  ];

  if (error) {
    return <div className="flex items-center justify-center h-96"><div className="text-center"><p className="text-red-400 mb-2">{error}</p><Button variant="outline" onClick={loadData}>Retry</Button></div></div>;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Your AI lead generation overview</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="success" className="gap-1">
            <Zap className="h-3 w-3" /> AI Active
          </Badge>
           <Button size="sm" className="gap-2" onClick={() => setShowFinder(true)}>
            <Sparkles className="h-4 w-4" /> AI Lead Finder
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {statCards.map((card, i) => (
          <Card key={i} className={`bg-gradient-to-br ${card.color} card-hover`}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-muted-foreground">{card.title}</span>
                <card.icon className={`h-4 w-4 ${card.iconColor}`} />
              </div>
              <p className="text-2xl font-bold">{card.value}</p>
              <div className="flex items-center gap-1 mt-1">
                {card.up ? (
                  <ArrowUp className="h-3 w-3 text-green-500" />
                ) : (
                  <ArrowDown className="h-3 w-3 text-red-500" />
                )}
                <span className={`text-xs ${card.up ? "text-green-500" : "text-red-500"}`}>
                  {card.change}
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Pipeline Kanban */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <BarChart3 className="h-5 w-5 text-primary" /> Lead Pipeline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {pipeline && Object.entries(pipeline).map(([status, count]: [string, any]) => (
                <div key={status} className="flex items-center gap-3">
                  <div className={`h-3 w-3 rounded-full ${
                    status === "new" ? "bg-blue-500" :
                    status === "contacted" ? "bg-yellow-500" :
                    status === "qualified" ? "bg-green-500" :
                    status === "converted" ? "bg-emerald-500" : "bg-red-500"
                  }`} />
                  <span className="flex-1 text-sm capitalize">{status}</span>
                  <span className="text-sm font-bold">{count as number}</span>
                  <div className="h-2 flex-1 rounded-full bg-secondary overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        status === "new" ? "bg-blue-500" :
                        status === "contacted" ? "bg-yellow-500" :
                        status === "qualified" ? "bg-green-500" :
                        status === "converted" ? "bg-emerald-500" : "bg-red-500"
                      }`}
                      style={{ width: `${(count as number) / (stats?.total_leads || 1) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <TrendingUp className="h-5 w-5 text-primary" /> Performance Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {[
                { label: "Open Rate", value: formatPercent(stats?.open_rate || 0), color: "text-blue-500" },
                { label: "Reply Rate", value: formatPercent(stats?.reply_rate || 0), color: "text-green-500" },
                { label: "Conversion Rate", value: formatPercent(stats?.conversion_rate || 0), color: "text-purple-500" },
                { label: "Bounce Rate", value: formatPercent(stats?.bounce_rate || 0), color: "text-red-500" },
              ].map((m, i) => (
                <div key={i} className="rounded-lg bg-secondary/50 p-4 text-center card-hover">
                  <p className={`text-2xl font-bold ${m.color}`}>{m.value}</p>
                  <p className="text-xs text-muted-foreground mt-1">{m.label}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Campaigns & Activity */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Activity className="h-5 w-5 text-primary" /> Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(activity.length > 0 ? activity : [
                { event_type: "info", event_name: "No recent activity yet", channel: null, extra_data: null, created_at: new Date().toISOString() },
              ]).map((item: any, i: number) => {
                const timeAgo = item.created_at ? formatTimeAgo(item.created_at) : "";
                const type = item.event_type || "info";
                return (
                <div key={i} className="flex items-center gap-3 p-3 rounded-lg hover:bg-accent/50 transition-colors">
                  <div className={`flex h-8 w-8 items-center justify-center rounded-full ${
                    type === "campaign" ? "bg-blue-500/10 text-blue-500" :
                    type === "lead" ? "bg-green-500/10 text-green-500" :
                    type === "reply" || type === "email" ? "bg-purple-500/10 text-purple-500" :
                    type === "ai" || type === "score" ? "bg-cyan-500/10 text-cyan-500" :
                    "bg-orange-500/10 text-orange-500"
                  }`}>
                    {type === "campaign" ? <Send className="h-4 w-4" /> :
                     type === "lead" ? <Users className="h-4 w-4" /> :
                     type === "reply" || type === "email" ? <MessageCircle className="h-4 w-4" /> :
                     type === "ai" || type === "score" ? <Zap className="h-4 w-4" /> :
                     <Activity className="h-4 w-4" />}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{item.event_name || item.event_type}</p>
                    {item.channel && <p className="text-xs text-muted-foreground">Channel: {item.channel}</p>}
                  </div>
                  <span className="text-xs text-muted-foreground">{timeAgo}</span>
                </div>
              )})}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <DollarSign className="h-5 w-5 text-primary" /> Revenue Overview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center mb-6">
              <p className="text-4xl font-bold gradient-text">
                {formatCurrency(stats?.current_mrr || 0)}
              </p>
              <p className="text-sm text-muted-foreground mt-1">Monthly Recurring Revenue</p>
            </div>
            <div className="space-y-3">
              {[
                { label: "Active Clients", value: formatNumber(clients.length), change: clients.length > 0 ? "Active" : "No clients yet" },
                { label: "Avg. Revenue/Client", value: clients.length > 0 ? formatCurrency((stats?.current_mrr || 0) / clients.length) : "$0", change: clients.length > 0 ? "Per client" : "Add clients to start" },
                { label: "Monthly Target", value: formatCurrency(stats?.current_mrr || 0), change: `$${2999 - (stats?.current_mrr || 0)} to go` },
              ].map((item, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
                  <div>
                    <p className="text-sm font-medium">{item.label}</p>
                    <p className="text-xs text-muted-foreground">{item.change}</p>
                  </div>
                  <p className="text-lg font-bold">{item.value}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
      {/* AI Lead Finder Modal */}
      {showFinder && (
        <div className={MODAL_STYLE + " !z-50"} onClick={() => { if (!finderLoading) setShowFinder(false); }}>
          <Card className="w-full max-w-2xl max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                <CardTitle>AI Lead Finder</CardTitle>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setShowFinder(false)} disabled={finderLoading}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Input */}
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium mb-1 block">Target Keywords *</label>
                  <Input
                    placeholder="e.g. lawyer, real estate, doctor, شركة عقار"
                    value={finderForm.keywords}
                    onChange={e => setFinderForm({...finderForm, keywords: e.target.value})}
                    disabled={finderLoading}
                  />
                  <p className="text-xs text-muted-foreground mt-1">Arabic keywords supported automatically</p>
                </div>
                <div>
                  <label className="text-sm font-medium mb-1 block">Location (optional)</label>
                  <Input
                    placeholder="e.g. Dubai, Riyadh, London, دبي"
                    value={finderForm.locations}
                    onChange={e => setFinderForm({...finderForm, locations: e.target.value})}
                    disabled={finderLoading}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-1 block">Max Leads: {finderForm.max_leads}</label>
                  <input
                    type="range"
                    min={1}
                    max={200}
                    value={finderForm.max_leads}
                    onChange={e => setFinderForm({...finderForm, max_leads: parseInt(e.target.value)})}
                    disabled={finderLoading}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground"><span>1</span><span>200</span></div>
                </div>
              </div>

              <Button className="w-full gap-2" onClick={handleFindLeads} disabled={finderLoading || !finderForm.keywords}>
                {finderLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                {finderLoading ? "Searching..." : "Find Leads with AI"}
              </Button>

              {/* Remaining limit info */}
              {stats?.total_leads !== undefined && (
                <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/50 text-sm">
                  <span>Your Plan: <strong>{TIER_NAMES[stats?.subscription_tier || "free"] || "Free"}</strong></span>
                  <span>Today: {stats?.total_leads || 0} / {finderTier === "free" && finderRemaining >= 999999 ? "♾️ Unlimited" : `${TIER_LIMITS[stats?.subscription_tier || "free"]}`} leads</span>
                </div>
              )}

              {/* Message */}
              {finderMsg && (
                <div className={`p-3 rounded-lg text-sm ${finderMsg.includes("Found") ? "bg-green-500/10 text-green-400 border border-green-500/20" : "bg-red-500/10 text-red-400 border border-red-500/20"}`}>
                  {finderMsg}
                </div>
              )}

              {/* Results */}
              {finderResults.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">Found Leads ({finderResults.length})</h3>
                    {!finderSaved && (
                      <Button size="sm" className="gap-1" onClick={() => { setFinderSaved(true); loadData(); }}>
                        <Check className="h-3 w-3" /> Saved to Database
                      </Button>
                    )}
                    {finderSaved && <Badge variant="success" className="gap-1"><Check className="h-3 w-3" /> Saved</Badge>}
                  </div>
                  <div className="overflow-x-auto border rounded-lg">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b bg-muted/50">
                          <th className="text-left p-2 font-medium">Name</th>
                          <th className="text-left p-2 font-medium">Email</th>
                          <th className="text-left p-2 font-medium">Website</th>
                          <th className="text-left p-2 font-medium">Score</th>
                          <th className="text-left p-2 font-medium">Source</th>
                        </tr>
                      </thead>
                      <tbody>
                        {finderResults.map((lead: any, i: number) => (
                          <tr key={i} className="border-b last:border-0 hover:bg-accent/50">
                            <td className="p-2 font-medium">{lead.name}</td>
                            <td className="p-2 text-muted-foreground">{lead.email || "-"}</td>
                            <td className="p-2 text-muted-foreground truncate max-w-[150px]">{lead.website || "-"}</td>
                            <td className="p-2">
                              <div className="flex items-center gap-1">
                                <div className="h-1.5 w-12 rounded-full bg-secondary overflow-hidden">
                                  <div className={`h-full rounded-full ${lead.score >= 70 ? "bg-green-500" : lead.score >= 40 ? "bg-yellow-500" : "bg-red-500"}`}
                                    style={{ width: `${lead.score}%` }} />
                                </div>
                                <span className="text-xs">{lead.score}</span>
                              </div>
                            </td>
                            <td className="p-2 text-muted-foreground">{lead.source || "ai_finder"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
