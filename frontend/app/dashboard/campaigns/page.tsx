"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { campaignsAPI } from "@/lib/api";
import { getStatusColor, formatDate, formatNumber } from "@/lib/utils";
import { Plus, Play, Pause, BarChart3, Send, Users, Loader2, X, Edit3, Trash2 } from "lucide-react";

const MODAL_STYLE = "fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm";

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ name: "", target_keywords: "", target_locations: "" });
  const [error, setError] = useState("");

  useEffect(() => { loadCampaigns(); }, []);

  const loadCampaigns = async () => {
    setError("");
    try { const res = await campaignsAPI.list({ per_page: 50 }); setCampaigns(res.data.items); }
    catch (err) { setError("Failed to load campaigns"); }
    finally { setLoading(false); }
  };

  const handleLaunch = async (id: number) => {
    try { await campaignsAPI.launch(id); loadCampaigns(); }
    catch (err) { setError("Failed to launch campaign"); }
  };

  const handlePause = async (id: number) => {
    try { await campaignsAPI.pause(id); loadCampaigns(); }
    catch (err) { setError("Failed to pause campaign"); }
  };

  const handleDeleteCampaign = async (id: number) => {
    if (!confirm("Delete this campaign?")) return;
    try { await campaignsAPI.delete(id); loadCampaigns(); }
    catch (err) { setError("Failed to delete campaign"); }
  };

  const resetForm = () => setForm({ name: "", target_keywords: "", target_locations: "" });

  const handleSave = async () => {
    if (!form.name) return;
    setSaving(true);
    try {
      const payload = { ...form, target_keywords: form.target_keywords.split(",").map(s => s.trim()).filter(Boolean), target_locations: form.target_locations.split(",").map(s => s.trim()).filter(Boolean) };
      if (showEdit) { await campaignsAPI.update(showEdit.id, payload); }
      else { await campaignsAPI.create(payload); }
      setShowCreate(false); setShowEdit(null); resetForm(); loadCampaigns();
    } catch (err) { console.error(err); }
    finally { setSaving(false); }
  };

  const openEdit = (c: any) => {
    setShowEdit(c);
    setForm({ name: c.name, target_keywords: (c.target_keywords || []).join(", "), target_locations: (c.target_locations || []).join(", ") });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Campaigns</h1>
          <p className="text-muted-foreground">{campaigns.length} campaigns</p>
        </div>
        <Button className="gap-2" onClick={() => { resetForm(); setShowCreate(true); setShowEdit(null); }}>
          <Plus className="h-4 w-4" /> New Campaign
        </Button>
      </div>

      {error && <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">{error}</div>}

      {loading ? (
        <div className="flex items-center justify-center h-64"><div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div>
      ) : campaigns.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Send className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No campaigns yet</h3>
            <p className="text-sm text-muted-foreground mb-4">Create your first campaign to start generating leads</p>
            <Button className="gap-2" onClick={() => { resetForm(); setShowCreate(true); }}><Plus className="h-4 w-4" /> Create Campaign</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {campaigns.map((campaign) => (
            <Card key={campaign.id} className="card-hover">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-lg">{campaign.name}</h3>
                      <Badge variant="outline" className={getStatusColor(campaign.status)}>{campaign.status}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-4">{campaign.target_keywords?.join(", ") || "No keywords"} • {campaign.target_locations?.join(", ") || "All locations"}</p>
                    <div className="flex items-center gap-6 text-sm">
                      <div className="flex items-center gap-1"><Users className="h-4 w-4 text-muted-foreground" /><span>{campaign.leads_processed} leads</span></div>
                      <div className="flex items-center gap-1"><Send className="h-4 w-4 text-muted-foreground" /><span>{campaign.emails_sent} sent</span></div>
                      <div className="flex items-center gap-1"><BarChart3 className="h-4 w-4 text-muted-foreground" /><span>{campaign.emails_opened} opened</span></div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {campaign.status === "draft" && <Button size="sm" className="gap-1" onClick={() => handleLaunch(campaign.id)}><Play className="h-3 w-3" /> Launch</Button>}
                    {campaign.status === "active" && <Button size="sm" variant="outline" className="gap-1" onClick={() => handlePause(campaign.id)}><Pause className="h-3 w-3" /> Pause</Button>}
                    <Button size="sm" variant="ghost" className="gap-1" onClick={() => openEdit(campaign)}><Edit3 className="h-3 w-3" /> Edit</Button>
                    <Button size="sm" variant="ghost" className="gap-1" onClick={() => handleDeleteCampaign(campaign.id)}><Trash2 className="h-3 w-3 text-red-400" /></Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {(showCreate || showEdit) && (
        <div className={MODAL_STYLE} onClick={() => { setShowCreate(false); setShowEdit(null); }}>
          <Card className="w-full max-w-md" onClick={e => e.stopPropagation()}>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>{showEdit ? "Edit Campaign" : "New Campaign"}</CardTitle>
              <Button variant="ghost" size="icon" onClick={() => { setShowCreate(false); setShowEdit(null); }}><X className="h-4 w-4" /></Button>
            </CardHeader>
            <CardContent className="space-y-3">
              <Input placeholder="Campaign Name *" value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
              <Input placeholder="Target Keywords (comma-separated)" value={form.target_keywords} onChange={e => setForm({...form, target_keywords: e.target.value})} />
              <Input placeholder="Target Locations (comma-separated)" value={form.target_locations} onChange={e => setForm({...form, target_locations: e.target.value})} />
              <div className="flex gap-2 justify-end pt-2">
                <Button variant="outline" onClick={() => { setShowCreate(false); setShowEdit(null); }}>Cancel</Button>
                <Button onClick={handleSave} disabled={saving || !form.name}>{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save"}</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
